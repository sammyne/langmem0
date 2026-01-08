"""Chat model that uses the Mem0-based OpenAI API.

This module provides a custom implementation of the ChatOpenAI class from the
langchain_openai library, integrating Mem0 memory management for enhanced
contextual understanding and response generation.
"""

import asyncio
import logging
import threading
from typing import Any, Self

import langchain_openai
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    BaseRunManager,
    CallbackManagerForLLMRun,
)
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult
from langchain_openai.chat_models.base import _convert_message_to_dict
from mem0 import AsyncMemory, Memory
from mem0.configs.base import MemoryConfig
from mem0.configs.prompts import MEMORY_ANSWER_PROMPT
from pydantic import Field, model_validator


logger = logging.getLogger(__name__)

_background_tasks = set()


class Mem0Ctx:
    """Context for mem0 operations."""

    def __init__(
        self, user_id: str | None, run_manager: BaseRunManager | None
    ) -> None:
        """Build a Mem0Ctx object from user_id and run_manager.

        Args:
            user_id: The user identifier.
            run_manager: The run manager for tracking execution.

        Raises:
            ValueError: If user_id is not provided.
        """
        self.run_id = str(run_manager.run_id) if run_manager else None
        self.metadata = (
            run_manager.inheritable_metadata | run_manager.metadata
            if run_manager
            else {}
        )

        if self.metadata:
            user_id = self.metadata.pop("user_id", user_id)

        if not user_id:
            raise ValueError("user_id must be provided")

        self.user_id = user_id


class ChatOpenAI(langchain_openai.ChatOpenAI):
    """Chat model that uses the Mem0-based OpenAI API."""

    user_id: str | None = Field(
        None, description="The user ID to use for the Mem0 API."
    )

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
            return await super()._agenerate(
                messages, stop, run_manager, **kwargs
            )

        ctx = Mem0Ctx(self.user_id, run_manager)
        logger.info(f"Generating response for user {ctx.user_id}")

        messages = _prepend_system_prompt_if_none(messages)

        open_ai_messages = [_convert_message_to_dict(v) for v in messages]

        await self._amemorize_nonblocking(ctx, open_ai_messages)
        relevant_memories = await self._arecall(ctx, open_ai_messages)
        logger.debug(
            f"Retrieved {len(relevant_memories)} "
            f"relevant memories for user {ctx.user_id}"
        )

        messages[-1].content = self._rewrite_query_with_memories(
            messages[-1].content, relevant_memories
        )

        return await super()._agenerate(messages, stop, run_manager, **kwargs)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from the model."""
        ctx = Mem0Ctx(self.user_id, run_manager)

        logger.info(
            f"Generating response for user {ctx.user_id} "
            f"and run-id={ctx.run_id}"
        )

        if not isinstance(messages[-1], HumanMessage):
            return super()._generate(messages, stop, run_manager, **kwargs)

        messages = _prepend_system_prompt_if_none(messages)

        open_ai_messages = [_convert_message_to_dict(v) for v in messages]
        self._memorize_nonblocking(ctx, open_ai_messages)
        relevant_memories = self._recall(ctx, open_ai_messages)
        logger.debug(
            f"Retrieved {len(relevant_memories)} "
            f"relevant memories for user {ctx.user_id}"
        )

        messages[-1].content = self._rewrite_query_with_memories(
            messages[-1].content, relevant_memories
        )

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
        """Initialize Mem0 memory instances.

        Returns:
            Self: The validated instance with Mem0 memory configured.
        """
        self._m0 = Memory.from_config(self.mem0)

        c = AsyncMemory._process_config(self.mem0)
        self._am0 = AsyncMemory(config=MemoryConfig(**c))

        return self

    async def _amemorize_nonblocking(
        self,
        ctx: Mem0Ctx,
        messages: list[dict[str, str]],
    ) -> None:
        async def add_task() -> None:
            logger.debug(f"Adding to memory non-blocking with {ctx.user_id=}")
            await self._am0.add(
                messages=messages,
                user_id=ctx.user_id,
                run_id=ctx.run_id,
                metadata=ctx.metadata,
            )

        # https://docs.python.org/3/library/asyncio-task.html#creating-tasks
        task = asyncio.create_task(add_task())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    async def _arecall(
        self,
        ctx: Mem0Ctx,
        messages: list[dict[str, str]],
        limit: int = 10,
    ) -> dict[str, Any]:
        conversation = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in messages[-6:]
        )

        # PASS RUN-ID WILL SCOPE SEARCHING WITHIN THE SPECIFIC RUN'S MEMORIES
        return await self._am0.search(
            conversation,
            user_id=ctx.user_id,
            # run_id=ctx.run_id,
            filters=ctx.metadata,
            limit=limit,
        )

    def _memorize_nonblocking(
        self,
        ctx: Mem0Ctx,
        messages: list[dict[str, str]],
    ) -> None:
        def add_task() -> None:
            logger.debug(f"Adding to memory non-blocking with {ctx.user_id}")
            self._m0.add(
                messages=messages,
                user_id=ctx.user_id,
                run_id=ctx.run_id,
                metadata=ctx.metadata,
            )

        threading.Thread(target=add_task, daemon=True).start()

    def _recall(
        self,
        ctx: Mem0Ctx,
        messages: list[dict[str, str]],
        limit: int = 10,
    ) -> dict[str, Any]:
        conversation = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in messages[-6:]
        )

        # PASS RUN-ID WILL SCOPE SEARCHING WITHIN THE SPECIFIC RUN'S MEMORIES
        return self._m0.search(
            conversation,
            user_id=ctx.user_id,
            filters=ctx.metadata,
            limit=limit,
        )

    def _rewrite_query_with_memories(
        self, user_question: str, relevant_memories: dict[str, Any]
    ) -> str:
        import json

        s = json.dumps(relevant_memories)
        print(f"relevant_memories: {s}")

        memorized = "\n".join(
            v["memory"] for v in relevant_memories["results"]
        )
        # 只有开启 graph 才会有 relations
        # entities=relevant_memories.get('relations', [])

        return (
            f"- Relevant Memories/Facts: {memorized}\n\n"
            f"- User Question: {user_question}"
        )


def _prepend_system_prompt_if_none(
    messages: list[BaseMessage],
) -> list[BaseMessage]:
    """Prepend a system prompt if there is none in the messages."""
    if messages and isinstance(messages[0], SystemMessage):
        return messages

    system_prompt = SystemMessage(content=MEMORY_ANSWER_PROMPT)
    return [system_prompt, *messages]
