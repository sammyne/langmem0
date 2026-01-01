import os

import dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from langmem0.tools import ManageMemoryTool

dotenv.load_dotenv()


def new_openai_like(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_API_BASE_URL"],
        model=os.environ["OPENAI_MODEL"],
        **kwargs,
    )


print("=" * 60)
print("LangChain Agent 示例 - 使用假的 LLM 和 MemoryStore")
print("=" * 60)

# 创建假的 LLM
model = new_openai_like()

# 创建 agent
print("\n[创建 Agent] 使用 create_tool_calling_agent")
agent = create_agent(
    model, tools=[ManageMemoryTool()], system_prompt="You are a helpful assistant."
)

r = agent.invoke(
    {"messages": [{"role": "user", "content": "请帮我计算 5 乘以 3 的结果"}]}
)

for v in r["messages"]:
    v.pretty_print()
