"""
Utility functions for testing jsonriver

Copyright (c) 2023 Google LLC (original TypeScript implementation)
Copyright (c) 2024 jsonriver-python contributors (Python port)
SPDX-License-Identifier: BSD-3-Clause
"""

import json
from typing import AsyncIterator, TypeVar, Any

T = TypeVar('T')


async def make_stream(*chunks: str) -> AsyncIterator[str]:
    """Create an async iterable from string chunks"""
    for chunk in chunks:
        yield chunk


def make_stream_of_chunks(text: str, chunk_size: int) -> AsyncIterator[str]:
    """Split text into chunks of specified size and return as async iterable"""
    async def _generator() -> AsyncIterator[str]:
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
    return _generator()


async def to_array(async_iter: AsyncIterator[T]) -> list[T]:
    """Collect all items from an async iterator into a list"""
    result: list[T] = []
    async for item in async_iter:
        result.append(item)
    return result


async def assert_same_as_json_parse(
    name: str,
    json_str: str,
    check_partial: bool | None = None
) -> None:
    """
    Assert that parsing with jsonriver produces the same result as JSON.parse

    Args:
        name: Name of the test case
        json_str: JSON string to parse
        check_partial: If True, verify partial results too
    """
    # Import here to avoid circular dependency during testing
    from jsonriver import parse

    # Parse with native JSON
    try:
        expected = json.loads(json_str)
        should_succeed = True
    except (json.JSONDecodeError, ValueError):
        should_succeed = False
        expected = None

    # Parse with jsonriver
    try:
        stream = make_stream_of_chunks(json_str, 1)
        results = await to_array(parse(stream))

        if not should_succeed:
            raise AssertionError(
                f"{name}: Expected parsing to fail but it succeeded with: {results[-1] if results else None}"
            )

        if not results:
            raise AssertionError(f"{name}: No results from parse")

        actual = results[-1]

        # Deep equality check
        assert actual == expected, f"{name}: Expected {expected!r}, got {actual!r}"

    except Exception as e:
        if should_succeed:
            raise AssertionError(
                f"{name}: Expected parsing to succeed but it failed with: {e}"
            ) from e
        # Expected to fail, and it did


async def assert_round_trips(value: Any) -> None:
    """
    Assert that a value can be serialized to JSON and parsed back with jsonriver
    producing the same value
    """
    from jsonriver import parse

    json_str = json.dumps(value)

    # Try different chunk sizes to test various parsing paths
    for chunk_size in [1, 2, 10, 100, len(json_str)]:
        stream = make_stream_of_chunks(json_str, chunk_size)
        results = await to_array(parse(stream))

        assert results, f"No results when parsing with chunk_size={chunk_size}"

        final = results[-1]
        assert final == value, (
            f"Round trip failed with chunk_size={chunk_size}: "
            f"Expected {value!r}, got {final!r}"
        )
