import langchain_openai
import threading
import asyncio
from pydantic import model_validator
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from typing import Any
from langchain_core.outputs import ChatResult
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
import logging
from mem0 import Memory,AsyncMemory
from mem0.configs.base import MemoryConfig 
from mem0.configs.prompts import  MEMORY_ANSWER_PROMPT
from typing_extensions import Self
from langchain_openai.chat_models.base import _convert_message_to_dict

logger = logging.getLogger(__name__)

_background_tasks = set()

class ChatOpenAI(langchain_openai.ChatOpenAI):
  """Chat model that uses the Mem0-based OpenAI API."""

  user_id: str
  """The user ID to use for the Mem0 API."""

  mem0: dict[str, Any]
  """The Mem0 configuration to use."""

  async def _agenerate(
      self,
      messages: list[BaseMessage],
      stop: list[str] | None = None,
      run_manager: AsyncCallbackManagerForLLMRun | None = None,
      **kwargs: Any,
  ) -> ChatResult:
    if not isinstance(messages[-1], HumanMessage):
      return await super()._agenerate(messages, stop, run_manager, **kwargs)

    logger.info(f"Generating response for user {self.user_id}")

    messages = _prepend_system_prompt_if_none(messages) 

    open_ai_messages = [_convert_message_to_dict(v) for v in messages]

    await self._amemorize_nonblocking(open_ai_messages, self.user_id)      
    relevant_memories = await self._arecall(open_ai_messages, self.user_id)
    logger.debug(f"Retrieved {len(relevant_memories)} relevant memories for user {self.user_id}")

    messages[-1].content = self._rewrite_query_with_memories(messages[-1].content, relevant_memories)

    return await super()._agenerate(messages, stop, run_manager, **kwargs)

  def _generate(
      self,
      messages: list[BaseMessage],
      stop: list[str] | None = None,
      run_manager: CallbackManagerForLLMRun | None = None,
      **kwargs: Any,
  ) -> ChatResult:
    """Generate a response from the model."""
    logger.info(f"Async generating response for user {self.user_id}")

    if not isinstance(messages[-1], HumanMessage):
      return super()._generate(messages, stop, run_manager, **kwargs)

    messages = _prepend_system_prompt_if_none(messages) 

    open_ai_messages = [_convert_message_to_dict(v) for v in messages]
    self._memorize_nonblocking(open_ai_messages, self.user_id)      
    relevant_memories = self._recall(open_ai_messages, self.user_id)
    logger.debug(f"Retrieved {len(relevant_memories)} relevant memories for user {self.user_id}")

    messages[-1].content = self._rewrite_query_with_memories(messages[-1].content, relevant_memories)

    return super()._generate(messages, stop, run_manager, **kwargs)

  @classmethod
  def get_lc_namespace(cls) -> list[str]:
      """Get the namespace of the LangChain object.

      Returns:
          `["langchain", "chat_models", "mem0-openai"]`
      """
      return ["langchain", "chat_models", "mem0-openai"]

  @classmethod
  def is_lc_serializable(cls) -> bool:
    """Return whether this model can be serialized by LangChain."""
    return False
  
  @model_validator(mode="after")
  def with_mem0(self) -> Self:
    self._m0 = Memory.from_config(self.mem0)

    c = AsyncMemory._process_config(self.mem0)
    self._am0 = AsyncMemory(config=MemoryConfig(**c))

    return self

  async def _amemorize_nonblocking(self, messages: list[dict[str,str]], user_id:str, agent_id=None, run_id=None, metadata=None):
        async def add_task():
            logger.debug(f"Adding to memory non-blocking with {self.user_id=}")
            await self._am0.add(
                messages=messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata,
            )
        
        # https://docs.python.org/3/library/asyncio-task.html#creating-tasks
        task = asyncio.create_task(add_task())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

  async def _arecall(self, messages: list[dict[str,str]], user_id: str, agent_id: str|None=None, run_id: str|None=None, filters: dict[str,Any]|None=None, limit: int = 10):
    conversation = '\n'.join(f"{message['role']}: {message['content']}" for message in messages[-6:])

    return await self._am0.search(conversation, user_id=user_id, agent_id=agent_id, run_id=run_id, filters=filters, limit=limit)
  
  def _memorize_nonblocking(self, messages: list[dict[str,str]], user_id:str, agent_id=None, run_id=None, metadata=None):
        def add_task():
            logger.debug(f"Adding to memory non-blocking with {self.user_id=}")
            self._m0.add(
                messages=messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata,
            )

        threading.Thread(target=add_task, daemon=True).start()
  
  def _recall(self, messages: list[dict[str,str]], user_id: str, agent_id: str|None=None, run_id: str|None=None, filters: dict[str,Any]|None=None, limit: int = 10):
    conversation = '\n'.join(f"{message['role']}: {message['content']}" for message in messages[-6:])

    return self._m0.search(conversation, user_id=user_id, agent_id=agent_id, run_id=run_id, filters=filters, limit=limit)
  
  def _rewrite_query_with_memories(self, user_question: str, relevant_memories) -> str:
    memorized = '\n'.join(v['memory'] for v in relevant_memories['results'])
    # 只有开启 graph 才会有 relations
    # entities=relevant_memories.get('relations', [])

    return f"- Relevant Memories/Facts: {memorized}\n\n- User Question: {user_question}"

def _prepend_system_prompt_if_none(
    messages: list[BaseMessage]
) -> list[BaseMessage]:
    """Prepend a system prompt if there is none in the messages."""
    if messages and isinstance(messages[0], SystemMessage):
      return messages

    system_prompt = SystemMessage(content=MEMORY_ANSWER_PROMPT)
    return [system_prompt]+messages