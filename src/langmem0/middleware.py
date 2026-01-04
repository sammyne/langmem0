from collections.abc import Callable
import logging
from typing import Awaitable,Any

from langgraph.runtime import Runtime
from mem0 import Memory
from langchain.messages import SystemMessage,HumanMessage
from langchain_openai.chat_models.base import _convert_message_to_dict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)

logger = logging.getLogger(__name__)

class Mem0Middleware(AgentMiddleware):
    def __init__(self, config: dict[str, Any]):
        self.m0 = Memory.from_config(config)

    # def aafter_agent(self, state: AgentState, runtime: Runtime) -> None:
    #     pass

    def after_agent(self, state: AgentState, runtime: Runtime) -> None:
        user_id = extract_user_id(runtime)
        if not user_id:
            return None
        
        interaction = [
            _convert_message_to_dict(v) for v in state["messages"]
        ]

        logger.debug(f"user-id={user_id}, interaction={interaction}")

        # https://docs.mem0.ai/integrations/langgraph#create-chatbot-function 
        self.m0.add(interaction, user_id=user_id)

    # async def awrap_model_call(
    #     self,
    #     request: ModelRequest,
    #     handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    # ) -> ModelCallResult:
    #     pass

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        if not isinstance(request.messages[-1], HumanMessage):
            return handler(request)

        user_id = extract_user_id(request.runtime)
        if not user_id:
            return handler(request)

        r = self.m0.search(request.messages[-1].content, user_id=user_id)
        if not r['results']:
            return handler(request)

        # ref: https://docs.langchain.com/oss/python/langchain/middleware/custom#working-with-system-messages
        # ref: https://docs.mem0.ai/core-concepts/memory-operations/search
        # ref: https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        addon_ctx = "Use the provided context to personalize your responses and remember user preferences and past interactions."
        for v in r['results']:
            addon_ctx += f"\n- {v['memory']}"

        logger.debug(f"user-id={user_id}")
        logger.debug(f"add-on ctx\n{addon_ctx}")
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": addon_ctx}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

def extract_user_id(rt: Runtime) -> str | None:
    """
    Extracts the user ID from the runtime context.

    Args:
        rt (Runtime): The runtime context.

    Returns:
        str | None: The user ID, or None if not found.
    """
    ctx = rt.context
    if not ctx:
        return None
    
    return ctx.user_id