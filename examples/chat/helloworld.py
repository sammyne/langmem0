"""Sample code reference: https://docs.mem0.ai/open-source/features/openai_compatibility."""

import os

import dotenv
from langchain_huggingface import HuggingFaceEmbeddings

from langmem0 import ChatOpenAI


dotenv.load_dotenv()

# Set log level to INFO and specify output format
# import logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# )


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
#             # Where to save data locally, remove if not necessary
#             persist_directory="./chroma",
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

model = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_API_BASE_URL"],
    model=os.environ["OPENAI_MODEL"],
    user_id="alice",
    mem0=config,
)


# Store preferences
_r = model.invoke("I love Indian food but I'm allergic to cheese.")

# Later conversation reuses the memory
r = model.invoke("Suggest dinner options in San Francisco.")

r.pretty_print()

# Sample output
# ================================== Ai Message
# ==================================
#
# Since you love Indian food and are allergic to cheese, here are some dinner
# options for you in San Francisco:
#
# *   **Indian Cuisine:** This is a great choice for you. Many dishes are
# naturally cheese-free. Look for tandoori items, curries made with coconut or
# yogurt bases (instead of cream), and dal dishes. Just be sure to confirm
# there is no paneer (Indian cheese) in your order.
#
# *   **Thai or Vietnamese Food:** These cuisines rarely use cheese. You can
# enjoy a variety of curries, pho, stir-fries, and fresh spring rolls without
# worrying about your allergy.
#
# *   **Mediterranean / Middle Eastern Food:** Excellent for a cheese-free
# meal. You can have grilled kebabs, falafel, hummus, and salads. Just make
# sure to request that they hold the feta cheese.
