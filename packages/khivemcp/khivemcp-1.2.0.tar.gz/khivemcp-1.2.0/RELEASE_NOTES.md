# khivemcp v1.2.1 - Batch Execution Fix

## 🐛 Critical Bugfix

**Fixed**: Batch execution with positional arguments
**Impact**: `[tool("foo"), tool("bar")]` now works correctly for `parallelizable=True` operations

**Details**: Batch execution paths were skipping positional argument mapping, causing validation errors. Now properly maps `_pos_*` keys to field names before schema validation, ensuring batch and single-call behavior is consistent.

**Example**:
```python
# Now works! ✅
[search("AI"), search("ML"), search("DL")]
```

## 📝 Documentation

- Fixed CLI docstring examples (removed incorrect "run" subcommand)
- Updated all examples to use correct syntax: `khivemcp config.json`

## 🧪 Testing

- 165 tests passing
- New test suite for batch execution with positional arguments

## Upgrade

```bash
pip install --upgrade khivemcp
# or
uv pip install --upgrade khivemcp
```

---

# khivemcp v1.2.0 - Research-Backed Optimizations

## 🚀 Core Features

**TypeScript-Style Schemas** (78.9% token reduction)
- Automatic TS syntax generation from Pydantic models
- Better LLM comprehension, massive token savings
- `@operation(schema=YourModel)` - works automatically

**Function Call Syntax** (52% token reduction)
- Natural Python syntax: `search("AI", limit=10)`
- Batch support: `[search("AI"), search("ML")]`
- More intuitive for code-trained models

**Parallel Execution** (2-10x performance)
- Add `parallelizable=True` to decorator
- Concurrent batch operations via `asyncio.gather()`
- Perfect for independent operations

**Union Schemas**
- Single operation, multiple input types
- `@operation(schema=SchemaA | SchemaB)`
- Type-safe routing with automatic validation

## 📚 Documentation Overhaul

**91% reduction**: 3,006 → 271 lines
- setup.md: 89% smaller
- features.md: 87% smaller
- deployment.md: 94% smaller
- What/Why/How format for clarity

## 🔧 Other Changes

- **License**: MIT → Apache 2.0
- **Examples**: Refactored search_group.py to demonstrate union schemas + parallel execution
- **Tests**: 163 passing, including new test suites for all features

## Breaking Changes

None - all features are opt-in via decorator parameters.

---

**Philosophy**: Easy to use means powerful features with minimal configuration and concise documentation.
