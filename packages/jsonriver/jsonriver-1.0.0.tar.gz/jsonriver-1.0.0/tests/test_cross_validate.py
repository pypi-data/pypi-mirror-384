"""
Cross-validation tests comparing Python implementation against Node.js jsonriver

These tests verify that the Python implementation produces identical results
to the original TypeScript/Node.js implementation.
"""

import json
import subprocess
import copy
import pytest
from jsonriver import parse
from tests.utils import make_stream_of_chunks, to_array


def parse_with_nodejs(json_str: str, chunk_size: int = 1) -> dict:
    """Parse JSON using the Node.js jsonriver implementation"""
    result = subprocess.run(
        ['node', 'test_bridge.mjs', json_str, str(chunk_size)],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(f"Node.js bridge failed: {result.stderr}")

    return json.loads(result.stdout)


async def parse_with_python(json_str: str, chunk_size: int = 1) -> list:
    """Parse JSON using Python implementation"""
    stream = make_stream_of_chunks(json_str, chunk_size)
    results = []
    async for value in parse(stream):
        # Make a deep copy since the parser reuses objects
        results.append(copy.deepcopy(value))
    return results


class TestCrossValidation:
    """Cross-validation tests against Node.js implementation"""

    @pytest.mark.asyncio
    async def test_simple_values(self):
        """Test simple JSON values match Node.js output"""
        test_cases = [
            'null',
            'true',
            'false',
            '123',
            '-456',
            '3.14',
            '1e10',
            '""',
            '"hello"',
            '"hello world"',
        ]

        for json_str in test_cases:
            print(f"Testing: {json_str}")

            # Parse with Node.js
            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success'], f"Node.js failed: {node_result.get('error')}"
            node_values = [json.loads(r) for r in node_result['results']]

            # Parse with Python
            py_values = await parse_with_python(json_str, 1)

            # Compare
            assert py_values == node_values, (
                f"Mismatch for {json_str}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_arrays(self):
        """Test arrays match Node.js output"""
        test_cases = [
            '[]',
            '[1]',
            '[1,2]',
            '[1,2,3]',
            '["a","b","c"]',
            '[null,true,false]',
            '[[],[]]',
            '[1,[2,[3]]]',
        ]

        for json_str in test_cases:
            print(f"Testing: {json_str}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_values = [json.loads(r) for r in node_result['results']]

            py_values = await parse_with_python(json_str, 1)

            assert py_values == node_values, (
                f"Mismatch for {json_str}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_objects(self):
        """Test objects match Node.js output"""
        test_cases = [
            '{}',
            '{"a":1}',
            '{"a":1,"b":2}',
            '{"name":"Alice","age":30}',
            '{"nested":{"key":"value"}}',
            '{"array":[1,2,3]}',
        ]

        for json_str in test_cases:
            print(f"Testing: {json_str}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_values = [json.loads(r) for r in node_result['results']]

            py_values = await parse_with_python(json_str, 1)

            assert py_values == node_values, (
                f"Mismatch for {json_str}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_complex_nested(self):
        """Test complex nested structures"""
        test_cases = [
            '{"user":{"name":"Bob","hobbies":["reading","coding"]}}',
            '{"a":[1,{"b":2},[3,4]]}',
            '[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]',
        ]

        for json_str in test_cases:
            print(f"Testing: {json_str}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_values = [json.loads(r) for r in node_result['results']]

            py_values = await parse_with_python(json_str, 1)

            assert py_values == node_values, (
                f"Mismatch for {json_str}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_escape_sequences(self):
        """Test string escape sequences"""
        test_cases = [
            r'"\""',
            r'"\\"',
            r'"\/"',
            r'"\n"',
            r'"\r"',
            r'"\t"',
            r'"\b"',
            r'"\f"',
            r'"\u0041"',
            r'"\u03B1"',
            r'"hello\nworld"',
        ]

        for json_str in test_cases:
            print(f"Testing: {json_str}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_values = [json.loads(r) for r in node_result['results']]

            py_values = await parse_with_python(json_str, 1)

            assert py_values == node_values, (
                f"Mismatch for {json_str}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test whitespace is handled correctly"""
        test_cases = [
            '  null  ',
            '\n\t[\n\t1\n\t]\n\t',
            '  {  "a"  :  1  }  ',
            ' [ 1 , 2 , 3 ] ',
        ]

        for json_str in test_cases:
            print(f"Testing: {repr(json_str)}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_values = [json.loads(r) for r in node_result['results']]

            py_values = await parse_with_python(json_str, 1)

            assert py_values == node_values, (
                f"Mismatch for {repr(json_str)}:\n"
                f"Node.js: {node_values}\n"
                f"Python:  {py_values}"
            )

    @pytest.mark.asyncio
    async def test_various_chunk_sizes(self):
        """Test that different chunk sizes produce consistent final results"""
        json_str = '{"name":"Alice","age":30,"items":[1,2,3],"active":true}'

        # Test with various chunk sizes
        for chunk_size in [1, 2, 5, 10, 100]:
            print(f"Testing chunk_size={chunk_size}")

            node_result = parse_with_nodejs(json_str, chunk_size)
            assert node_result['success']
            node_final = json.loads(node_result['results'][-1])

            py_values = await parse_with_python(json_str, chunk_size)
            py_final = py_values[-1]

            assert py_final == node_final, (
                f"Final value mismatch at chunk_size={chunk_size}:\n"
                f"Node.js: {node_final}\n"
                f"Python:  {py_final}"
            )

    @pytest.mark.asyncio
    async def test_error_cases(self):
        """Test that invalid JSON produces errors in both implementations"""
        invalid_cases = [
            '{"a":',
            '[1,2,',
            'null null',
            'tru',
            '{a:1}',
        ]

        for json_str in invalid_cases:
            print(f"Testing invalid: {json_str}")

            # Node.js should fail
            node_result = parse_with_nodejs(json_str, 1)
            node_failed = not node_result['success']

            # Python should fail
            py_failed = False
            try:
                await parse_with_python(json_str, 1)
            except (ValueError, RuntimeError):
                py_failed = True

            assert node_failed and py_failed, (
                f"Error handling mismatch for {json_str}:\n"
                f"Node.js failed: {node_failed}\n"
                f"Python failed: {py_failed}"
            )

    @pytest.mark.asyncio
    async def test_numbers_precision(self):
        """Test that numbers are parsed with correct precision"""
        test_cases = [
            '0',
            '1',
            '-1',
            '123',
            '-456',
            '3.14',
            '-2.718',
            '1e10',
            '1e-10',
            '1.23e45',
            '0.000001',
            '1000000',
        ]

        for json_str in test_cases:
            print(f"Testing number: {json_str}")

            node_result = parse_with_nodejs(json_str, 1)
            assert node_result['success']
            node_final = json.loads(node_result['results'][-1])

            py_values = await parse_with_python(json_str, 1)
            py_final = py_values[-1]

            # Use approximate equality for floating point
            if isinstance(node_final, float):
                assert abs(py_final - node_final) < 1e-10, (
                    f"Number mismatch for {json_str}: {node_final} vs {py_final}"
                )
            else:
                assert py_final == node_final
