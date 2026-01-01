from typing import Any
from collections.abc import Callable

from langgraph.runtime import Runtime
from mem0 import Memory
from langchain.messages import SystemMessage
from langchain_openai.chat_models.base import _convert_message_to_dict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)


class Mem0Middleware(AgentMiddleware):
    def __init__(self, store: Memory):
        self.store = store

    def before_agent(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        print("before_agent")
        pass

    def after_agent(self, state: AgentState, runtime: Runtime) -> None:
        ctx = runtime.context
        if not ctx:
            return None
        
        interaction = [
            _convert_message_to_dict(v) for v in state["messages"]
        ]

        # https://docs.mem0.ai/integrations/langgraph#create-chatbot-function 
        self.store.add(interaction, user_id=ctx.user_id)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        ctx = request.runtime.context
        if not ctx:
            return handler(request)

        # ref: https://docs.langchain.com/oss/python/langchain/middleware/custom#working-with-system-messages
        # ref: https://docs.mem0.ai/core-concepts/memory-operations/search
        # ref: https://docs.mem0.ai/integrations/langgraph#create-chatbot-function
        r = self.store.search(request.messages[-1].content, user_id=ctx.user_id)
        if not r['results']:
            return handler(request)

        addon_ctx = "Use the provided context to personalize your responses and remember user preferences and past interactions."
        for v in r['results']:
            addon_ctx += f"\n- {v['memory']}"

        print(f"wrap_model_call, user-id={ctx.user_id}")
        print(f"add-on ctx\n{addon_ctx}")
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": addon_ctx}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))
