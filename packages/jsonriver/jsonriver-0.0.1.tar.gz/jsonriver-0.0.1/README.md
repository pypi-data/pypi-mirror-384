# jsonriver - Python Streaming JSON Parser

Parse JSON incrementally as it streams in, e.g. from a network request or a language model. Gives you a sequence of increasingly complete values.

This is a Python port of the TypeScript [jsonriver](https://github.com/rictic/jsonriver) library.

## Features

- **Incremental parsing**: Get progressively complete JSON values as data arrives
- **Zero dependencies**: Uses only Python standard library
- **Fully typed**: Complete type hints with mypy strict mode compliance
- **Memory efficient**: Reuses objects and arrays when possible
- **Correct**: Final result matches `json.loads()` exactly
- **Fast**: Optimized for performance with minimal overhead

## Installation

### From PyPI (recommended)

Using uv:
```bash
uv add jsonriver
```

Using pip:
```bash
pip install jsonriver
```

### From source

Using uv:
```bash
git clone https://github.com/chrisschnabl/streamjson.git
cd streamjson
uv pip install -e .
```

Using pip:
```bash
git clone https://github.com/chrisschnabl/streamjson.git
cd streamjson
pip install -e .
```

## Usage

```python
import asyncio
import json
from jsonriver import parse


async def make_stream(text: str, chunk_size: int):
    """Simulate a streaming source"""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


async def main():
    json_str = '{"name": "Alice", "age": 30}'

    stream = make_stream(json_str, chunk_size=3)
    async for value in parse(stream):
        print(json.dumps(value))
    # Output shows incremental results:
    # {}
    # {"name": "Al"}
    # {"name": "Alice"}
    # {"name": "Alice", "age": 30.0}


asyncio.run(main())
```

## How it Works

jsonriver yields a sequence of increasingly complete JSON values. Consider this JSON:

```json
{"name": "Alex", "keys": [1, 20, 300]}
```

If you parse this one byte at a time, it would yield:

```json
{}
{"name": ""}
{"name": "A"}
{"name": "Al"}
{"name": "Ale"}
{"name": "Alex"}
{"name": "Alex", "keys": []}
{"name": "Alex", "keys": [1]}
{"name": "Alex", "keys": [1, 20]}
{"name": "Alex", "keys": [1, 20, 300]}
```

## Invariants

The library maintains these guarantees:

1. **Type stability**: Future versions will have the same type (never changes string → array)
2. **Atomic values**: `null`, `true`, `false`, and numbers are only yielded when complete
3. **String growth**: Strings may be replaced with longer versions
4. **Array append-only**: Arrays only modified by appending or mutating the last element
5. **Object append-only**: Objects only modified by adding properties or mutating the last one
6. **Complete keys**: Object properties only added once key and value type are known

## Error Handling

The parser throws errors for invalid JSON, matching `json.loads()` behavior:

```python
async def example_error():
    try:
        stream = make_stream('{"invalid": }', 1)
        async for value in parse(stream):
            print(value)
    except ValueError as e:
        print(f"Parse error: {e}")
```

## Development

### Setup

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parse.py -v

# Run with coverage
python -m pytest tests/ --cov=src/jsonriver
```

### Type Checking

```bash
# Check types with mypy
mypy src/jsonriver --strict
```

### Running Examples

```bash
python example_jsonriver.py
```

## Project Structure

```
src/jsonriver/
  __init__.py       # Public API exports
  parse.py          # JSON parser implementation
  tokenize.py       # JSON tokenizer implementation

tests/
  test_parse.py     # Parser tests
  test_tokenize.py  # Tokenizer tests
  utils.py          # Test utilities
```

## API Reference

### `parse(stream: AsyncIterator[str]) -> AsyncIterator[JsonValue]`

Incrementally parse a single JSON value from the given iterable of string chunks.

**Parameters:**
- `stream`: An async iterator that yields string chunks containing JSON data

**Yields:**
- Increasingly complete JSON values as more input is parsed

**Raises:**
- `ValueError`: If the input is not valid JSON
- `RuntimeError`: For internal parsing errors

**Example:**
```python
async def parse_json():
    json_str = '{"a": 1, "b": 2}'

    async def stream():
        for char in json_str:
            yield char

    async for value in parse(stream()):
        print(value)
```

### Type Definitions

```python
JsonValue = Union[
    None,
    bool,
    float,
    str,
    list['JsonValue'],
    dict[str, 'JsonValue']
]

JsonObject = dict[str, JsonValue]
```

## Performance

jsonriver is designed for performance:

- Processes input synchronously in batches when available
- Reuses objects and arrays to minimize allocations
- Minimal overhead compared to standard `json.loads()`
- Efficient state machine implementation

In practice, jsonriver adds negligible overhead to the parsing process while providing valuable incremental updates.

## Use Cases

- **Streaming APIs**: Parse JSON from network requests as data arrives
- **Large payloads**: Start processing data before complete response
- **Real-time UIs**: Update UI as JSON parses
- **LLM responses**: Parse structured output from language models
- **Progress indicators**: Show parsing progress to users
- **Server-sent events**: Handle JSON in SSE streams

## Comparison with Alternatives

| Feature | jsonriver | json.loads | ijson |
|---------|-----------|------------|-------|
| Incremental parsing | ✅ | ❌ | ✅ |
| Complete values | ✅ | ✅ | ❌ |
| No dependencies | ✅ | ✅ | ❌ |
| Type hints | ✅ | ✅ | ❌ |
| Memory efficient | ✅ | ❌ | ✅ |

## License

BSD-3-Clause License

- Original TypeScript implementation: Copyright (c) 2023 Google LLC
- Python port: Copyright (c) 2024 jsonriver-python contributors

See LICENSE file for full license text.

## Credits

This is a Python port of the excellent [jsonriver](https://github.com/rictic/jsonriver) TypeScript library by Peter Burns (@rictic).

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest tests/ -v`
2. Type checking passes: `mypy src/jsonriver --strict`
3. Code follows existing style
4. New features include tests

## Changelog

### 0.0.1 (2024)

- Initial Python port from TypeScript
- Full type hints with mypy strict mode
- Comprehensive test suite (37 tests)
- Complete documentation
- Zero dependencies
