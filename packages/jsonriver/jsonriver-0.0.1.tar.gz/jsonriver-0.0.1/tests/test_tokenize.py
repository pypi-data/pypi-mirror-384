"""
Tests for the JSON tokenizer

Copyright (c) 2023 Google LLC (original TypeScript implementation)
Copyright (c) 2024 jsonriver-python contributors (Python port)
SPDX-License-Identifier: BSD-3-Clause
"""

import json
import pytest
from jsonriver.tokenize import (
    JsonTokenType,
    tokenize,
    TokenHandler,
)
from tests.utils import make_stream, to_array


class TestTokenHandler(TokenHandler):
    """Test implementation of TokenHandler that records tokens"""

    def __init__(self):
        self.tokens: list[dict] = []

    def handle_null(self) -> None:
        self.tokens.append({"type": JsonTokenType.Null, "value": None})

    def handle_boolean(self, value: bool) -> None:
        self.tokens.append({"type": JsonTokenType.Boolean, "value": value})

    def handle_number(self, value: float) -> None:
        self.tokens.append({"type": JsonTokenType.Number, "value": value})

    def handle_string_start(self) -> None:
        self.tokens.append({"type": JsonTokenType.StringStart, "value": None})

    def handle_string_middle(self, value: str) -> None:
        self.tokens.append({"type": JsonTokenType.StringMiddle, "value": value})

    def handle_string_end(self) -> None:
        self.tokens.append({"type": JsonTokenType.StringEnd, "value": None})

    def handle_array_start(self) -> None:
        self.tokens.append({"type": JsonTokenType.ArrayStart, "value": None})

    def handle_array_end(self) -> None:
        self.tokens.append({"type": JsonTokenType.ArrayEnd, "value": None})

    def handle_object_start(self) -> None:
        self.tokens.append({"type": JsonTokenType.ObjectStart, "value": None})

    def handle_object_end(self) -> None:
        self.tokens.append({"type": JsonTokenType.ObjectEnd, "value": None})


async def tokenize_to_list(*chunks: str) -> list[dict]:
    """Tokenize chunks and return list of tokens"""
    handler = TestTokenHandler()
    tokenizer = tokenize(make_stream(*chunks), handler)

    while not tokenizer.is_done():
        await tokenizer.pump()

    return handler.tokens


class TestTokenize:
    """Test suite for tokenize function"""

    @pytest.mark.asyncio
    async def test_tokenize_null(self):
        """Test tokenizing null"""
        tokens = await tokenize_to_list("null")
        assert tokens == [{"type": JsonTokenType.Null, "value": None}]

    @pytest.mark.asyncio
    async def test_tokenize_empty_array(self):
        """Test tokenizing empty array"""
        tokens = await tokenize_to_list("[]")
        assert tokens == [
            {"type": JsonTokenType.ArrayStart, "value": None},
            {"type": JsonTokenType.ArrayEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_array_with_one_element(self):
        """Test tokenizing array with one element"""
        tokens = await tokenize_to_list("[null]")
        assert tokens == [
            {"type": JsonTokenType.ArrayStart, "value": None},
            {"type": JsonTokenType.Null, "value": None},
            {"type": JsonTokenType.ArrayEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_array_with_two_elements(self):
        """Test tokenizing array with two elements"""
        tokens = await tokenize_to_list("[null, true]")
        assert tokens == [
            {"type": JsonTokenType.ArrayStart, "value": None},
            {"type": JsonTokenType.Null, "value": None},
            {"type": JsonTokenType.Boolean, "value": True},
            {"type": JsonTokenType.ArrayEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_empty_string(self):
        """Test tokenizing empty string"""
        tokens = await tokenize_to_list('""')
        assert tokens == [
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_string_with_one_character(self):
        """Test tokenizing string with one character"""
        tokens = await tokenize_to_list('"a"')
        assert tokens == [
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_chunked_string(self):
        """Test tokenizing string split across chunks"""
        tokens = await tokenize_to_list('"', 'a', '"')
        assert tokens == [
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_string_with_two_characters(self):
        """Test tokenizing string with two characters"""
        tokens = await tokenize_to_list('"', 'a', 'b', '"')
        assert tokens == [
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringMiddle, "value": "b"},
            {"type": JsonTokenType.StringEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_string_with_escapes(self):
        """Test tokenizing string with escape sequences"""
        tokens = await tokenize_to_list(json.dumps('"\\\n\u2028\t'))
        assert tokens == [
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": '"'},
            {"type": JsonTokenType.StringMiddle, "value": '\\'},
            {"type": JsonTokenType.StringMiddle, "value": '\n'},
            {"type": JsonTokenType.StringMiddle, "value": '\u2028'},
            {"type": JsonTokenType.StringMiddle, "value": '\t'},
            {"type": JsonTokenType.StringEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_empty_object(self):
        """Test tokenizing empty object"""
        tokens = await tokenize_to_list('{}')
        assert tokens == [
            {"type": JsonTokenType.ObjectStart, "value": None},
            {"type": JsonTokenType.ObjectEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_object_with_one_property(self):
        """Test tokenizing object with one key-value pair"""
        tokens = await tokenize_to_list('{"a": null}')
        assert tokens == [
            {"type": JsonTokenType.ObjectStart, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.Null, "value": None},
            {"type": JsonTokenType.ObjectEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_object_with_two_properties(self):
        """Test tokenizing object with two key-value pairs"""
        tokens = await tokenize_to_list('{"a": null, "b": true}')
        assert tokens == [
            {"type": JsonTokenType.ObjectStart, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.Null, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "b"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.Boolean, "value": True},
            {"type": JsonTokenType.ObjectEnd, "value": None},
        ]

    @pytest.mark.asyncio
    async def test_tokenize_number(self):
        """Test tokenizing a number"""
        tokens = await tokenize_to_list('123')
        assert tokens == [{"type": JsonTokenType.Number, "value": 123}]

    @pytest.mark.asyncio
    async def test_tokenize_number_split_across_chunks(self):
        """Test tokenizing number split across chunks"""
        tokens = await tokenize_to_list('1', '23')
        assert tokens == [{"type": JsonTokenType.Number, "value": 123}]

    @pytest.mark.asyncio
    async def test_tokenize_decimal_number_split(self):
        """Test tokenizing decimal number split across chunks"""
        tokens = await tokenize_to_list('3.', '14')
        assert tokens == [{"type": JsonTokenType.Number, "value": 3.14}]

    @pytest.mark.asyncio
    async def test_tokenize_negative_number(self):
        """Test tokenizing negative number"""
        tokens = await tokenize_to_list('-42')
        assert tokens == [{"type": JsonTokenType.Number, "value": -42}]

    @pytest.mark.asyncio
    async def test_tokenize_number_with_exponent(self):
        """Test tokenizing number with exponent"""
        tokens = await tokenize_to_list('6.02e23')
        assert tokens == [{"type": JsonTokenType.Number, "value": 6.02e23}]

    @pytest.mark.asyncio
    async def test_tokenize_true(self):
        """Test tokenizing true"""
        tokens = await tokenize_to_list('true')
        assert tokens == [{"type": JsonTokenType.Boolean, "value": True}]

    @pytest.mark.asyncio
    async def test_tokenize_false(self):
        """Test tokenizing false"""
        tokens = await tokenize_to_list('false')
        assert tokens == [{"type": JsonTokenType.Boolean, "value": False}]

    @pytest.mark.asyncio
    async def test_tokenize_complex_nested_structure(self):
        """Test tokenizing complex nested JSON"""
        tokens = await tokenize_to_list('{"a":[1,2],"b":{"c":null}}')

        expected = [
            {"type": JsonTokenType.ObjectStart, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "a"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.ArrayStart, "value": None},
            {"type": JsonTokenType.Number, "value": 1},
            {"type": JsonTokenType.Number, "value": 2},
            {"type": JsonTokenType.ArrayEnd, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "b"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.ObjectStart, "value": None},
            {"type": JsonTokenType.StringStart, "value": None},
            {"type": JsonTokenType.StringMiddle, "value": "c"},
            {"type": JsonTokenType.StringEnd, "value": None},
            {"type": JsonTokenType.Null, "value": None},
            {"type": JsonTokenType.ObjectEnd, "value": None},
            {"type": JsonTokenType.ObjectEnd, "value": None},
        ]

        assert tokens == expected
