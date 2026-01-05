# LangMem0

## Quickstart

```bash
uv pip install -e .

# if you prefer sync APIs
uv run examples/middleware/helloworld_sync.py

# or you prefer async APIs
uv run examples/middleware/helloworld_async.py
```

## FAQ
### Why not provide tool-based API like langmem
Tool-based API has a problem: system prompt needs augumenting with memories using a separate middleware as demonstrated
by [LangMem's Hot Path Quickstart](https://langchain-ai.github.io/langmem/hot_path_quickstart/#agent).

## References
- [LangChain Chatbot](https://chat.langchain.com/?threadId=e7011d54-12ce-4c14-8d2a-324996e0d0de)
- [LangChain forum](https://forum.langchain.com/c/oss-product-help-lc-and-lg/langchain/14)
- [Mem0 Open Source](https://docs.mem0.ai/open-source/overview)
