import os

import dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dataclasses import dataclass

from langmem0.middleware import Mem0Middleware
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.checkpoint.memory import MemorySaver
import logging

dotenv.load_dotenv()


# 设置日志级别为 INFO，并指定输出格式
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@dataclass
class Context:
    user_id: str


def new_openai_like(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_API_BASE_URL"],
        model=os.environ["OPENAI_MODEL"],
        **kwargs,
    )


model = new_openai_like()

# https://github.com/mem0ai/mem0/blob/v1.0.0/mem0/configs/llms/openai.py#L6
llm = {
    "provider": "openai",
    "config": {
        "model": os.environ["OPENAI_MODEL"],
        "temperature": 0.1,
        "api_key": os.environ["OPENAI_API_KEY"],
        "openai_base_url": os.environ["OPENAI_API_BASE_URL"],
    },
}


embedding_model_name = "sentence-transformers/all-mpnet-base-v2"
# model_name='BAAI/bge-small-en-v1.5'
embedding = HuggingFaceEmbeddings(model_name=embedding_model_name)

# https://github.com/mem0ai/mem0/blob/v1.0.0/mem0/configs/vector_stores/langchain.py#L6
# https://docs.mem0.ai/components/vectordbs/dbs/langchain
# vector_store = {
#     "provider": "langchain",
#     "config": {
#         "client": Chroma(
#             collection_name="mem0",
#             embedding_function=embedding,
#             persist_directory="./chroma",  # Where to save data locally, remove if not necessary
#         )
#     },
# }

# https://github.com/mem0ai/mem0/blob/v1.0.0/mem0/configs/vector_stores/faiss.py#L6
# https://docs.mem0.ai/components/vectordbs/dbs/faiss
vector_store = {
    "provider": "faiss",
    "config": {"path": "./_data/faiss", "embedding_model_dims": 768},
}

embedder = {
    "provider": "huggingface",
    "config": {"model": embedding_model_name},
}

config = {
    "vector_store": vector_store,
    "llm": llm,
    "embedder": embedder,
}

agent = create_agent(
    model,
    middleware=[Mem0Middleware(config)],
    system_prompt="You are a helpful assistant.",
    context_schema=Context,
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "thread-a"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "Know which display mode I prefer?"}]},
    config=config,
    context=Context(user_id="test"),
)

for v in response["messages"]:
    v.pretty_print()

r = agent.invoke(
    {"messages": [{"role": "user", "content": "dark. Remember that."}]},
    # We will continue the conversation (thread-a) by using the config with
    # the same thread_id
    config=config,
    context=Context(user_id="test"),
)

print("----------")
for v in r["messages"]:
    v.pretty_print()

# New thread = new conversation!
new_config = {"configurable": {"thread_id": "thread-b"}}
# The agent will only be able to recall
# whatever it explicitly saved using the manage_memories tool
response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Hey there. Do you remember me? What are my preferences?",
            }
        ]
    },
    config=new_config,
    context=Context(user_id="test"),
)

# print(response["messages"][-1].content)
for v in response["messages"]:
    v.pretty_print()
