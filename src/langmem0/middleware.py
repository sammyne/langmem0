"""Middleware for integrating Mem0 memory with LangChain agents.

This module provides the Mem0Middleware class which automatically stores
conversations and retrieves relevant memories during model calls to provide
personalized responses.
"""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai.chat_models.base import _convert_message_to_dict
from langgraph.runtime import Runtime
from mem0 import AsyncMemory, Memory
from mem0.configs.base import MemoryConfig


logger = logging.getLogger(__name__)


class Mem0Middleware(AgentMiddleware):
    """Middleware for integrating Mem0 memory with LangChain agents.

    This middleware automatically stores conversations and retrieves relevant
    memories during model calls to provide personalized responses.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the Mem0 middleware.

        Args:
            config (dict[str, Any]): Mem0 configuration dictionary.
        """
        self.m0 = Memory.from_config(config)

        c = AsyncMemory._process_config(config)
        self.am0 = AsyncMemory(config=MemoryConfig(**c))

    async def aafter_agent(self, state: AgentState, runtime: Runtime) -> None:
        """Async handler called after agent execution.

        Args:
            state (AgentState): The agent state.
            runtime (Runtime): The runtime context.

        Returns:
            None: Returns None if user ID is not found.
        """
        if not (user_id := extract_user_id(runtime)):
            return None

        interaction = [_convert_message_to_dict(v) for v in state["messages"]]

        logger.debug(f"user-id={user_id}, interaction={interaction}")

        # https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        # https://docs.mem0.ai/open-source/features/async-memory
        await self.am0.add(interaction, user_id=user_id)

    def after_agent(self, state: AgentState, runtime: Runtime) -> None:
        """Handler called after agent execution.

        Args:
            state (AgentState): The agent state.
            runtime (Runtime): The runtime context.

        Returns:
            None: Returns None if user ID is not found.
        """
        user_id = extract_user_id(runtime)
        if not user_id:
            return None

        interaction = [_convert_message_to_dict(v) for v in state["messages"]]

        logger.debug(f"user-id={user_id}, interaction={interaction}")

        # https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        self.m0.add(interaction, user_id=user_id)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Async wrapper for model calls with memory context.

        Args:
            request (ModelRequest): The model request.
            handler (Callable): The next handler in the chain.

        Returns:
            ModelCallResult: The result of the model call.
        """
        if not isinstance(request.messages[-1], HumanMessage):
            return await handler(request)

        if not (user_id := extract_user_id(request.runtime)):
            return await handler(request)

        r = await self.am0.search(
            request.messages[-1].content, user_id=user_id
        )
        if not r["results"]:
            return await handler(request)

        # ref: https://docs.langchain.com/oss/python/langchain/middleware/custom#working-with-system-messages
        # ref: https://docs.mem0.ai/core-concepts/memory-operations/search
        # ref: https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        addon_ctx = (
            "Use the provided context to personalize your responses "
            "and remember user preferences and past interactions."
        )
        for v in r["results"]:
            addon_ctx += f"\n- {v['memory']}"

        logger.debug(f"user-id={user_id}")
        logger.debug(f"add-on ctx\n{addon_ctx}")
        new_content = [
            *list(request.system_message.content_blocks),
            {"type": "text", "text": addon_ctx}
        ]
        new_system_message = SystemMessage(content=new_content)
        return await handler(
            request.override(system_message=new_system_message)
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """Wrapper for model calls with memory context.

        Args:
            request (ModelRequest): The model request.
            handler (Callable): The next handler in the chain.

        Returns:
            ModelCallResult: The result of the model call.
        """
        if not isinstance(request.messages[-1], HumanMessage):
            return handler(request)

        user_id = extract_user_id(request.runtime)
        if not user_id:
            return handler(request)

        r = self.m0.search(request.messages[-1].content, user_id=user_id)
        if not r["results"]:
            return handler(request)

        # ref: https://docs.langchain.com/oss/python/langchain/middleware/custom#working-with-system-messages
        # ref: https://docs.mem0.ai/core-concepts/memory-operations/search
        # ref: https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        addon_ctx = (
            "Use the provided context to personalize your responses "
            "and remember user preferences and past interactions."
        )
        for v in r["results"]:
            addon_ctx += f"\n- {v['memory']}"

        logger.debug(f"user-id={user_id}")
        logger.debug(f"add-on ctx\n{addon_ctx}")
        new_content = [
            *list(request.system_message.content_blocks),
            {"type": "text", "text": addon_ctx}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))


def extract_user_id(rt: Runtime) -> str | None:
    """Extracts the user ID from the runtime context.

    Args:
        rt (Runtime): The runtime context.

    Returns:
        str | None: The user ID, or None if not found.
    """
    ctx = rt.context
    if not ctx:
        return None

    return ctx.user_id
