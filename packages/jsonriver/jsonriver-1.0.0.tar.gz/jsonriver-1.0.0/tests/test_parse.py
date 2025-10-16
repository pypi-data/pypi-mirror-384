"""
Tests for the JSON parser

Copyright (c) 2023 Google LLC (original TypeScript implementation)
Copyright (c) 2024 jsonriver-python contributors (Python port)
SPDX-License-Identifier: BSD-3-Clause
"""

import copy
import pytest
from jsonriver import parse
from tests.utils import (
    assert_round_trips,
    assert_same_as_json_parse,
    make_stream_of_chunks,
    to_array,
)


async def map_structural_clone(async_iter):
    """Yield deep copies of values from async iterator"""
    async for val in async_iter:
        yield copy.deepcopy(val)


class TestParse:
    """Test suite for parse function"""

    @pytest.mark.asyncio
    async def test_round_tripping(self):
        """Test that various JSON values can be serialized and parsed back"""
        json_values = [
            {"a": [{"b": ""}], "c": ""},
            # null
            None,
            # booleans
            True,
            False,
            # numbers
            0,
            1,
            -1,
            123,
            100e100,
            # strings
            "",
            "a",
            "ab",
            "a\nb",
            # arrays
            [],
            [None],
            [None, True],
            [None, True, 'a b c d e\n]["\\"] f g'],
            # objects
            {},
            {"a": None},
            {"a": None, "b": True},
            {"a": None, "b": True, "c": 'a b c d e\n]["\\"] f g'},
            # nested arrays and objects
            [[], {}],
            [{}, []],
            {"a": []},
            {"a": [], "b": {}},
            {"a": {}, "b": []},
            {
                "a": [None, True, 'a b c d e\n]["\\"]}{}}{{}} f g'],
                "b": {"c": 'a b c d e\n]["\\"] f g'},
            },
            {"a": [{"b": ""}], "c": ""},
            {
                "a": {
                    "b": {
                        "c": {
                            "d": {
                                "e": {
                                    "f": {"v": {"w": {"x": {"y": {"z": None}}}}},
                                }
                            }
                        }
                    }
                }
            },
        ]

        for i, json_value in enumerate(json_values):
            print(f"Testing case {i}: {type(json_value).__name__}")
            await assert_round_trips(json_value)

    @pytest.mark.asyncio
    async def test_first_64k_characters(self):
        """Test that first 64k characters behave properly"""
        # For the first 64Ki characters, check that they round trip,
        # and that they're treated the same as json.loads when inserted in
        # a string literal directly, and when decoded using a \\u escape.

        # Test a representative sample to keep test time reasonable
        # Test control characters, ASCII, and some Unicode
        test_chars = list(range(0, 32))  # Control characters
        test_chars.extend(range(32, 128))  # ASCII
        test_chars.extend([0x80, 0x100, 0x1000, 0xFFFF])  # Some Unicode points

        for i in test_chars:
            charcode_str = chr(i)
            hex_str = f"{i:04x}"

            # Test literal character (if it's a valid JSON string character)
            if i >= 0x20 and i != 0x22 and i != 0x5C:  # Not control, quote, or backslash
                await assert_same_as_json_parse(
                    f"literal U+{hex_str}",
                    f'"{charcode_str}"',
                    None,
                )

            # Test \\u escape
            await assert_same_as_json_parse(
                f"\\u escape U+{hex_str}",
                f'"\\u{hex_str}"',
                None,
            )

    @pytest.mark.asyncio
    async def test_partial_results(self):
        """Test that partial results are yielded correctly"""
        input_to_outputs = [
            (None, [None]),
            (True, [True]),
            (False, [False]),
            ("abc", ["", "a", "ab", "abc"]),
            ([], [[]]),
            (
                ["a", "b", "c"],
                [
                    [],
                    [""],
                    ["a"],
                    ["a", ""],
                    ["a", "b"],
                    ["a", "b", ""],
                    ["a", "b", "c"],
                ],
            ),
            (
                {"greeting": "hi!", "name": "G"},
                [
                    {},
                    {"greeting": ""},
                    {"greeting": "h"},
                    {"greeting": "hi"},
                    {"greeting": "hi!"},
                    {"greeting": "hi!", "name": ""},
                    {"greeting": "hi!", "name": "G"},
                ],
            ),
            (
                {"a": ["a", {"b": ["c"]}]},
                [
                    {},
                    {"a": []},
                    {"a": [""]},
                    {"a": ["a"]},
                    {"a": ["a", {}]},
                    {"a": ["a", {"b": []}]},
                    {"a": ["a", {"b": [""]}]},
                    {"a": ["a", {"b": ["c"]}]},
                ],
            ),
        ]

        for val, expected_vals in input_to_outputs:
            import json
            string_stream = make_stream_of_chunks(json.dumps(val), 1)
            partial_values = await to_array(
                map_structural_clone(parse(string_stream))
            )

            assert partial_values == expected_vals, (
                f"Parsing {json.dumps(val)} failed.\n"
                f"Expected: {expected_vals}\n"
                f"Got: {partial_values}"
            )

    @pytest.mark.asyncio
    async def test_deep_nesting(self):
        """Test that deeply nested structures can be parsed"""
        # Test that we can parse deeply nested structures (> 100 levels)
        depth = 1_000
        deep_array = "[" * depth + "1" + "]" * depth

        stream = make_stream_of_chunks(deep_array, 100)
        result = None
        async for val in parse(stream):
            result = val

        assert result is not None, "Should parse deeply nested array"

        # Verify depth by walking down
        current = result
        for i in range(depth):
            if not isinstance(current, list):
                assert current == 1, f"At depth {i}, should reach value 1"
                break
            current = current[0]

        assert current == 1, "At max depth, should reach value 1"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that invalid JSON raises errors"""
        invalid_jsons = [
            '{"a":',  # Incomplete
            '{"a": 1, }',  # Trailing comma in object
            '[1, 2, ]',  # Trailing comma in array
            '{"a": undefined}',  # Invalid value
            '{123: "value"}',  # Non-string key
            '"unclosed string',  # Unclosed string
            'null null',  # Multiple values
            'tru',  # Incomplete literal
            '{a: 1}',  # Unquoted key
        ]

        for invalid_json in invalid_jsons:
            with pytest.raises((ValueError, RuntimeError)):
                stream = make_stream_of_chunks(invalid_json, 1)
                results = []
                async for val in parse(stream):
                    results.append(val)
                # If we get here without exception, that's a failure
                pytest.fail(f"Expected error for invalid JSON: {invalid_json}")

    @pytest.mark.asyncio
    async def test_numbers(self):
        """Test various number formats"""
        numbers = [
            ("0", 0),
            ("123", 123),
            ("-123", -123),
            ("123.456", 123.456),
            ("-123.456", -123.456),
            ("1e10", 1e10),
            ("1E10", 1e10),
            ("1e+10", 1e+10),
            ("1e-10", 1e-10),
            ("123.456e10", 123.456e10),
        ]

        for json_str, expected in numbers:
            stream = make_stream_of_chunks(json_str, 1)
            results = await to_array(parse(stream))
            assert len(results) > 0
            assert results[-1] == expected, f"Failed to parse {json_str}"

    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test that whitespace is properly ignored"""
        json_with_whitespace = [
            ('  null  ', None),
            ('\n\t[\n\t1\n\t,\n\t2\n\t]\n\t', [1, 2]),
            ('  {  "a"  :  1  }  ', {"a": 1}),
        ]

        for json_str, expected in json_with_whitespace:
            stream = make_stream_of_chunks(json_str, 1)
            results = await to_array(parse(stream))
            assert len(results) > 0
            assert results[-1] == expected

    @pytest.mark.asyncio
    async def test_escape_sequences(self):
        """Test string escape sequences"""
        escapes = [
            (r'"\""', '"'),
            (r'"\\"', '\\'),
            (r'"\/"', '/'),
            (r'"\b"', '\b'),
            (r'"\f"', '\f'),
            (r'"\n"', '\n'),
            (r'"\r"', '\r'),
            (r'"\t"', '\t'),
            (r'"\u0041"', 'A'),
            (r'"\u03B1"', 'α'),
        ]

        for json_str, expected in escapes:
            stream = make_stream_of_chunks(json_str, 1)
            results = await to_array(parse(stream))
            assert len(results) > 0
            assert results[-1] == expected, f"Failed to parse {json_str}"
