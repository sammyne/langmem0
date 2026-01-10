# LangMem0

📚 [Documentation](https://sammyne.github.io/langmem0/)

[![PyPI version](https://badge.fury.io/py/langmem0.svg)](https://pypi.org/project/langmem0/)
![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
[![Lint with Ruff](https://github.com/sammyne/langmem0/actions/workflows/lint.yml/badge.svg)](https://github.com/sammyne/langmem0/actions/workflows/lint.yml)

## Installation

Install via `uv`

```bash
uv add langmem0
```

Install via `pip`

```bash
pip install langmem0
```

## Examples quickstart

### 0. Environment

- uv >= 0.9

### 1. Clone the repository

```bash
git clone https://github.com/sammyne/langmem0.git
cd langmem0
```

### 2. Install dependencies

```bash
uv pip install -e .
```

### 3. Set up environment variables

Create a `.env` file in the project root with your OpenAI configuration:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 4. Run examples

LangMem0 provides two main ways to integrate memory into your LangChain applications:

#### Middleware Examples

Use `Mem0Middleware` to enable memory in LangChain agent conversations. This approach provides fine-grained control over memory operations.

```bash
# Synchronous example
uv run examples/middleware/helloworld.py

# Asynchronous example
uv run examples/middleware/helloworld_async.py
```

These examples demonstrate:
- Using `Mem0Middleware` to intercept and augment agent messages with memories
- How agents can remember and retrieve information across conversations
- Different thread contexts for separate conversation memories
- Integration with LangGraph checkpoints

#### Chat Examples

Use `ChatOpenAI` with built-in Mem0 memory capabilities for a simpler integration path.

```bash
# Basic synchronous example
uv run examples/chat/helloworld.py

# Basic asynchronous example
uv run examples/chat/helloworld_async.py

# Advanced synchronous with RunnableConfig:**
uv run examples/chat/runnable_config.py

# Advanced asynchronous with RunnableConfig:**
uv run examples/chat/runnable_config_async.py
```

These examples demonstrate:
- Direct integration with OpenAI-compatible chat models
- Memory-enabled conversations with minimal setup
- Using `RunnableConfig` for thread management
- Both sync and async API patterns

## FAQ
### Why not provide tool-based API like langmem
Tool-based API has a problem: system prompt needs augumenting with memories using a separate middleware as demonstrated
by [LangMem's Hot Path Quickstart](https://langchain-ai.github.io/langmem/hot_path_quickstart/#agent).

## References
- [LangChain Chatbot](https://chat.langchain.com/?threadId=e7011d54-12ce-4c14-8d2a-324996e0d0de)
- [LangChain forum](https://forum.langchain.com/c/oss-product-help-lc-and-lg/langchain/14)
- [Mem0 Open Source](https://docs.mem0.ai/open-source/overview)
