"""Sample code reference: https://docs.mem0.ai/open-source/features/openai_compatibility."""

import asyncio
import logging
import os

import dotenv
from langchain_core.runnables import RunnableConfig

from langmem0 import ChatOpenAI


dotenv.load_dotenv()

# Set log level to INFO and specify output format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    """Main async function to demonstrate chat with memory."""
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

    # embedding_model_name='BAAI/bge-small-en-v1.5'
    embedding_model_name = "sentence-transformers/all-mpnet-base-v2"

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

    # Initialize the chatbot without user_id.
    model = ChatOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_API_BASE_URL"],
        model=os.environ["OPENAI_MODEL"],
        mem0=config,
    )

    # Store preferences.
    # Make sure to pass the user_id in the config's metadata
    # since there's no global user-id set on model.
    c = RunnableConfig(metadata={"user_id": "bob"})
    _r = await model.ainvoke(
        "I love Indian food but I'm allergic to cheese.", config=c
    )

    print("*" * 100)
    # Later conversation reuses the memory
    # Make sure to pass the user_id in the config's metadata
    # since there's no global user-id set on model.
    c = RunnableConfig(metadata={"user_id": "bob"})
    r = await model.ainvoke(
        "Suggest dinner options in San Francisco.", config=c
    )

    r.pretty_print()

    # Sample output
    # ================================== Ai Message ==================================  # noqa: E501
    #
    # Since you love Indian food and are allergic to cheese, here are some
    # dinner options for you in San Francisco:
    #
    # *   **Indian Cuisine:** This is a great choice for you. Many dishes are
    # naturally cheese-free. Look for tandoori items, curries made with
    # coconut or yogurt bases (instead of cream), and dal dishes. Just be
    # sure to confirm there is no paneer (Indian cheese) in your order.
    #
    # *   **Thai or Vietnamese Food:** These cuisines rarely use cheese. You
    # can enjoy a variety of curries, pho, stir-fries, and fresh spring
    # rolls without worrying about your allergy.
    #
    # *   **Mediterranean / Middle Eastern Food:** Excellent for a cheese-free
    # meal. You can have grilled kebabs, falafel, hummus, and salads. Just make
    # sure to request that they hold the feta cheese.


if __name__ == "__main__":
    asyncio.run(main())
