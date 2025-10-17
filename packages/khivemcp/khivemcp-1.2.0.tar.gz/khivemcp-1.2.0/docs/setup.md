# Setup Guide

## Installation

```bash
pip install khivemcp

# Or with uv (recommended)
uv pip install khivemcp
```

## Quick Start

**1. Create your service** (`calculator.py`):

```python
from khivemcp import ServiceGroup, operation
from pydantic import BaseModel

class MathOp(BaseModel):
    a: float
    b: float

class Calculator(ServiceGroup):
    @operation(name="add", schema=MathOp)
    async def add(self, request: MathOp):
        return {"result": request.a + request.b}
```

**2. Create config** (`config.json`):

```json
{
  "name": "calculator",
  "class_path": "calculator:Calculator"
}
```

The `class_path` format is `module:ClassName` - khivemcp imports `Calculator`
from `calculator.py`.

**3. Test locally**:

```bash
khivemcp config.json
```

**4. Add to Claude Desktop**
(`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "calculator": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "khivemcp.cli", "/absolute/path/to/config.json"]
    }
  }
}
```

**Important**: Use absolute paths. Find them with:

- Python path: `which python` (with venv activated)
- Config path: `pwd` (in your project directory)

Restart Claude Desktop and ask: "Use the calculator to add 15 and 27"

## Next Steps

- [Advanced Features](features.md) - TypeScript schemas, parallel execution,
  union types
- [Deployment](deployment.md) - Docker, HTTP, production
