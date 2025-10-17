# Advanced Features

khivemcp includes research-backed optimizations for efficient MCP servers.

## TypeScript-Style Schemas

**What**: Schemas are automatically formatted in compact TypeScript syntax.
**Why**: 78.9% token reduction vs JSON Schema + better LLM comprehension.
**How**: Automatic when you use `@operation(schema=YourModel)`.

```python
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    categories: list[str] | None = None

@operation(name="search", schema=SearchRequest)
async def search(self, request: SearchRequest):
    return {"results": [...]}
```

**Generated documentation**:

```typescript
query: string
limit?: int = 10
categories?: string[] | null
```

## Function Call Syntax

**What**: LLMs use natural Python syntax instead of verbose JSON. **Why**: 52%
token reduction + more intuitive for code-trained models. **How**: Automatic -
no configuration needed.

```python
# Instead of: {"query": "AI", "limit": 10}
search("AI", limit=10)
```

## Parallel Execution

**What**: Enable batch operations for concurrent execution. **Why**: 2-10x
faster for independent operations. **How**: Add `parallelizable=True` to
decorator.

```python
@operation(name="search", schema=SearchRequest, parallelizable=True)
async def search(self, request: SearchRequest):
    return await self.search_api(request.query)
```

**Usage**:

```python
# LLM can now batch requests - all execute concurrently
[search("AI"), search("ML"), search("DL")]
```

## Union Schemas

**What**: Accept multiple request types in a single operation. **Why**: Flexible
interfaces, fewer endpoints, type-safe routing. **How**: Use Python union types
(`|`) with Pydantic models.

```python
SearchRequest = ExaSearchRequest | PerplexitySearchRequest

@operation(name="search", schema=SearchRequest)
async def search(self, request: ExaSearchRequest | PerplexitySearchRequest):
    if isinstance(request, ExaSearchRequest):
        return await self.exa_search(request)
    return await self.perplexity_search(request)
```

Both schemas documented automatically. Full example:
[search_group.py](../examples/groups/search_group.py)

## Stateful Groups

Groups maintain state across operations:

```python
class StatefulGroup(ServiceGroup):
    def __init__(self, config=None):
        super().__init__(config)
        self.cache = {}  # State persists across calls

    @operation(name="store")
    async def store(self, request: dict):
        self.cache[request["key"]] = request["value"]
        return {"stored": True}
```

## Lifecycle Hooks

Manage resources with startup/shutdown:

```python
class MyGroup(ServiceGroup):
    async def startup(self):
        self.db = await connect_database()

    async def shutdown(self):
        await self.db.close()
```

## Multi-Group Services

Combine multiple groups in one server (YAML):

```yaml
name: "my_service"
groups:
  math:
    class_path: "calculator:Calculator"
  storage:
    class_path: "storage:StorageGroup"
```

Exposes `math.*` and `storage.*` operations from one server.

---

That's it. These features work automatically - just use the decorators and write
your logic.
