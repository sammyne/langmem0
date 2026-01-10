# LangMem0 - Agent Coding Guidelines

## Build, Lint, and Test Commands

### Package Management
- `uv sync` - Install dependencies from pyproject.toml
- `uv pip install -e .` - Install package in editable mode

### Linting and Formatting
- `uv run ruff check` - Run linting checks (Google Python style)
- `uv run ruff format` - Auto-format code
- `uv run ruff format --check` - Check formatting without modifying
- `uv run ruff check --fix` - Auto-fix linting issues

### Testing
- Currently no test files exist in the project
- To run tests when added: `uv run pytest` (assuming pytest is configured)
- Single test: `uv run pytest tests/test_module.py::test_function`

### Running Examples
- `uv run examples/middleware/helloworld.py` - Sync middleware example
- `uv run examples/middleware/helloworld_async.py` - Async middleware example
- `uv run examples/chat/helloworld.py` - Sync chat example
- `uv run examples/chat/helloworld_async.py` - Async chat example
- `uv run examples/chat/runnable_config.py` - Runnable config example
- `uv run examples/chat/runnable_config_async.py` - Async runnable config example

## Code Style Guidelines

### Language and Version
- Python 3.13+
- Modern type hints with union operators (`|` instead of `Union`)
- Collection types from `collections.abc` (e.g., `Callable`, `Awaitable`)

### Formatting (Ruff with Google Style Guide)
- Line length: 79 characters
- Indentation: 4 spaces
- Quotes: Double quotes for strings and docstrings
- Trailing commas: Enabled for multi-line structures

### Imports
- Order: stdlib → third-party → first-party
- Use `from collections.abc` for abstract types
- Separate import groups with blank lines
- Sort alphabetically within groups
- No unused imports
- Use absolute imports for first-party modules

```python
# Standard library
import logging
from collections.abc import Callable
from typing import Any

# Third-party
from langchain.agents import create_agent
from pydantic import Field

# First-party
from langmem0.middleware import Mem0Middleware
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `Mem0Middleware`, `ChatOpenAI`)
- Functions/variables: `snake_case` (e.g., `get_user_id`, `context_data`)
- Private methods: Leading underscore (e.g., `_extract_user_id`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `_background_tasks`)
- Type variables: `PascalCase` with `_T` suffix if applicable

### Docstrings (Google Style)
- Module docstring at top of file
- Class docstrings with brief description
- Function docstrings with Args, Returns, and Raises sections
- Use double quotes

```python
"""Brief module description.

More details about the module.
"""

def my_function(param1: str, param2: int) -> bool:
    """Brief description.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something goes wrong.
    """
```

### Type Annotations
- Required for all function parameters and return types
- Use `|` for unions instead of `Union[...]`
- Use `list[str]` instead of `List[str]`
- Use `dict[str, Any]` instead of `Dict[str, Any]`
- Use `str | None` instead of `Optional[str]`
- Field types in Pydantic models with `Field()` for descriptions

### Error Handling
- Validate early, raise exceptions for invalid inputs
- Use `ValueError` for invalid arguments
- Use type checking with `isinstance()` before type-specific operations
- Log errors with appropriate level (DEBUG, INFO, WARNING, ERROR)

### Logging
- Module-level logger: `logger = logging.getLogger(__name__)`
- Use f-strings for log messages
- Include relevant context in debug logs (user_id, run_id, etc.)

### Async/Sync Patterns
- Provide both sync and async implementations where applicable
- Use `asyncio.create_task()` for non-blocking background operations
- Use `threading.Thread(target=..., daemon=True)` for sync background tasks
- Async functions use `await` for I/O operations

### Module Structure
- `__all__` list to define public API
- Private helpers as module-level functions with leading underscores
- Classes and functions organized logically (helpers → main exports)

### Pydantic Models
- Use `Field()` for field descriptions and defaults
- Use `model_validator(mode="after")` for post-init validation
- Type hint all fields
- Use `| None` for optional fields

### File Organization
- Source code in `src/langmem0/`
- Examples in `examples/` (organized by feature)
- Docs in `docs/`
- No test directory yet (add `tests/` when needed)

### Environment Variables
- Use `python-dotenv` to load `.env` files
- Access via `os.environ["KEY"]` (will raise if missing)
- Document required env vars in README

### Comments
- Keep comments concise and relevant
- Avoid obvious comments (`# increment i`)
- Use inline comments for complex logic
- Reference external URLs with `# ref: https://...`
