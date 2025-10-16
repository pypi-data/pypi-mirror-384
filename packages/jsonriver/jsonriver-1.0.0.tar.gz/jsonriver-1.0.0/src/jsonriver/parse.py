"""
JSON parser for streaming incremental parsing

Copyright (c) 2023 Google LLC (original TypeScript implementation)
Copyright (c) 2024 jsonriver-python contributors (Python port)
SPDX-License-Identifier: BSD-3-Clause
"""

from __future__ import annotations
from typing import AsyncIterator, Union, cast
from enum import IntEnum

from .tokenize import (
    JsonTokenType,
    json_token_type_to_string,
    Tokenizer,
    tokenize,
)


# Type definitions for JSON values
JsonValue = Union[None, bool, float, str, list['JsonValue'], dict[str, 'JsonValue']]
JsonObject = dict[str, JsonValue]


async def parse(stream: AsyncIterator[str]) -> AsyncIterator[JsonValue]:
    """
    Incrementally parse a single JSON value from the given iterable of string chunks.

    Yields a sequence of increasingly complete JSON values as more of the input
    can be parsed. The final value yielded will be the same as running json.loads
    on the entire input as a single string. If the input is not valid JSON,
    throws an error in the same way that json.loads would, though the error
    message is not guaranteed to be the same.

    When possible (i.e. with objects and arrays), the yielded JSON values will
    be reused. This means that if you store a reference to a yielded value, it
    will be updated in place as more of the input is parsed.

    As with json.loads, this throws if non-whitespace trailing content is found.

    For performance, it parses as much of the string that's synchronously
    available before yielding. So the sequence of partially-complete values
    that you'll see will vary based on how the input is grouped into stream
    chunks.

    The following invariants will also be maintained:

    1. Future versions of a value will have the same type. i.e. we will never
       yield a value as a string and then later replace it with an array.
    2. true, false, null, and numbers are atomic, we don't yield them until
       we have the entire value.
    3. Strings may be replaced with a longer string, with more characters (in
       the Python sense) appended.
    4. Arrays are only modified by either appending new elements, or
       replacing/mutating the element currently at the end.
    5. Objects are only modified by either adding new properties, or
       replacing/mutating the most recently added property.
    6. As a consequence of 1 and 5, we only add a property to an object once we
       have the entire key and enough of the value to know that value's type.
    """
    parser = _Parser(stream)
    async for value in parser:
        yield value


class _StateEnum(IntEnum):
    """Parser state machine states"""
    Initial = 0
    InString = 1
    InArray = 2
    InObjectExpectingKey = 3
    InObjectExpectingValue = 4


class _State:
    """Base class for parser states"""
    type: _StateEnum
    value: JsonValue | tuple[str, JsonObject] | None


class _InitialState(_State):
    """Initial state before any parsing"""
    def __init__(self) -> None:
        self.type = _StateEnum.Initial
        self.value = None


class _InStringState(_State):
    """State while parsing a string"""
    def __init__(self) -> None:
        self.type = _StateEnum.InString
        self.value = ''


class _InArrayState(_State):
    """State while parsing an array"""
    def __init__(self) -> None:
        self.type = _StateEnum.InArray
        self.value: list[JsonValue] = []


class _InObjectExpectingKeyState(_State):
    """State while parsing an object, expecting a key"""
    def __init__(self) -> None:
        self.type = _StateEnum.InObjectExpectingKey
        self.value: JsonObject = {}


class _InObjectExpectingValueState(_State):
    """State while parsing an object, expecting a value"""
    def __init__(self, key: str, obj: JsonObject) -> None:
        self.type = _StateEnum.InObjectExpectingValue
        self.value = (key, obj)


# Sentinel value to distinguish "not set" from "set to None/null"
_UNSET = object()


class _Parser:
    """
    Incremental JSON parser

    Implements the AsyncIterator protocol to yield progressively
    more complete JSON values as input is consumed.
    """

    def __init__(self, text_stream: AsyncIterator[str]) -> None:
        self._state_stack: list[_State] = [_InitialState()]
        self._toplevel_value: JsonValue | object = _UNSET
        self.tokenizer = tokenize(text_stream, self)
        self._finished = False
        self._progressed = False

    async def __anext__(self) -> JsonValue:
        """Get next progressively complete value"""
        if self._finished:
            raise StopAsyncIteration

        while True:
            self._progressed = False
            await self.tokenizer.pump()

            if self._progressed:
                if self._toplevel_value is _UNSET:
                    raise RuntimeError(
                        'Internal error: toplevel_value should not be unset '
                        'after progressing'
                    )
                return self._toplevel_value  # type: ignore

            if len(self._state_stack) == 0:
                await self.tokenizer.pump()
                self._finished = True
                raise StopAsyncIteration

    def __aiter__(self) -> '_Parser':
        """Return self as async iterator"""
        return self

    # TokenHandler protocol implementation

    def handle_null(self) -> None:
        """Handle null token"""
        self._handle_value_token(JsonTokenType.Null, None)

    def handle_boolean(self, value: bool) -> None:
        """Handle boolean token"""
        self._handle_value_token(JsonTokenType.Boolean, value)

    def handle_number(self, value: float) -> None:
        """Handle number token"""
        self._handle_value_token(JsonTokenType.Number, value)

    def handle_string_start(self) -> None:
        """Handle string start token"""
        state = self._current_state()
        if not self._progressed and state.type != _StateEnum.InObjectExpectingKey:
            self._progressed = True

        if state.type == _StateEnum.Initial:
            self._state_stack.pop()
            self._toplevel_value = self._progress_value(
                JsonTokenType.StringStart, None
            )

        elif state.type == _StateEnum.InArray:
            v = self._progress_value(JsonTokenType.StringStart, None)
            arr = cast(list[JsonValue], state.value)
            arr.append(v)

        elif state.type == _StateEnum.InObjectExpectingKey:
            self._state_stack.append(_InStringState())

        elif state.type == _StateEnum.InObjectExpectingValue:
            key, obj = cast(tuple[str, JsonObject], state.value)
            sv = self._progress_value(JsonTokenType.StringStart, None)
            obj[key] = sv

        elif state.type == _StateEnum.InString:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(JsonTokenType.StringStart)} '
                f'token in the middle of string'
            )

    def handle_string_middle(self, value: str) -> None:
        """Handle string middle token"""
        state = self._current_state()

        if not self._progressed:
            if len(self._state_stack) >= 2:
                prev = self._state_stack[-2]
                if prev.type != _StateEnum.InObjectExpectingKey:
                    self._progressed = True
            else:
                self._progressed = True

        if state.type != _StateEnum.InString:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(JsonTokenType.StringMiddle)} '
                f'token when not in string'
            )

        assert isinstance(state.value, str)
        state.value += value

        parent_state = self._state_stack[-2] if len(self._state_stack) >= 2 else None
        self._update_string_parent(state.value, parent_state)

    def handle_string_end(self) -> None:
        """Handle string end token"""
        state = self._current_state()

        if state.type != _StateEnum.InString:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(JsonTokenType.StringEnd)} '
                f'token when not in string'
            )

        self._state_stack.pop()
        parent_state = self._state_stack[-1] if self._state_stack else None
        assert isinstance(state.value, str)
        self._update_string_parent(state.value, parent_state)

    def handle_array_start(self) -> None:
        """Handle array start token"""
        self._handle_value_token(JsonTokenType.ArrayStart, None)

    def handle_array_end(self) -> None:
        """Handle array end token"""
        state = self._current_state()
        if state.type != _StateEnum.InArray:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(JsonTokenType.ArrayEnd)} token'
            )
        self._state_stack.pop()

    def handle_object_start(self) -> None:
        """Handle object start token"""
        self._handle_value_token(JsonTokenType.ObjectStart, None)

    def handle_object_end(self) -> None:
        """Handle object end token"""
        state = self._current_state()

        if state.type in (_StateEnum.InObjectExpectingKey, _StateEnum.InObjectExpectingValue):
            self._state_stack.pop()
        else:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(JsonTokenType.ObjectEnd)} token'
            )

    # Private helper methods

    def _current_state(self) -> _State:
        """Get current parser state"""
        if not self._state_stack:
            raise ValueError('Unexpected trailing input')
        return self._state_stack[-1]

    def _handle_value_token(self, token_type: JsonTokenType, value: JsonValue) -> None:
        """Handle a complete value token"""
        state = self._current_state()

        if not self._progressed:
            self._progressed = True

        if state.type == _StateEnum.Initial:
            self._state_stack.pop()
            self._toplevel_value = self._progress_value(token_type, value)

        elif state.type == _StateEnum.InArray:
            v = self._progress_value(token_type, value)
            arr = cast(list[JsonValue], state.value)
            arr.append(v)

        elif state.type == _StateEnum.InObjectExpectingValue:
            key, obj = cast(tuple[str, JsonObject], state.value)
            if token_type != JsonTokenType.StringStart:
                self._state_stack.pop()
                new_state = _InObjectExpectingKeyState()
                new_state.value = obj
                self._state_stack.append(new_state)

            v = self._progress_value(token_type, value)
            obj[key] = v

        elif state.type == _StateEnum.InString:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(token_type)} '
                f'token in the middle of string'
            )

        elif state.type == _StateEnum.InObjectExpectingKey:
            raise ValueError(
                f'Unexpected {json_token_type_to_string(token_type)} '
                f'token in the middle of object expecting key'
            )

    def _update_string_parent(self, updated: str, parent_state: _State | None) -> None:
        """Update parent container with updated string value"""
        if parent_state is None:
            self._toplevel_value = updated

        elif parent_state.type == _StateEnum.InArray:
            arr = cast(list[JsonValue], parent_state.value)
            arr[-1] = updated

        elif parent_state.type == _StateEnum.InObjectExpectingValue:
            key, obj = cast(tuple[str, JsonObject], parent_state.value)
            obj[key] = updated
            if self._state_stack and self._state_stack[-1] == parent_state:
                self._state_stack.pop()
                new_state = _InObjectExpectingKeyState()
                new_state.value = obj
                self._state_stack.append(new_state)

        elif parent_state.type == _StateEnum.InObjectExpectingKey:
            if self._state_stack and self._state_stack[-1] == parent_state:
                self._state_stack.pop()
                obj = cast(JsonObject, parent_state.value)
                self._state_stack.append(
                    _InObjectExpectingValueState(updated, obj)
                )

    def _progress_value(self, token_type: JsonTokenType, value: JsonValue) -> JsonValue:
        """Create initial value for a token and push appropriate state"""
        if token_type == JsonTokenType.Null:
            return None

        elif token_type == JsonTokenType.Boolean:
            return value

        elif token_type == JsonTokenType.Number:
            return value

        elif token_type == JsonTokenType.StringStart:
            string_state = _InStringState()
            self._state_stack.append(string_state)
            return ''

        elif token_type == JsonTokenType.ArrayStart:
            array_state = _InArrayState()
            self._state_stack.append(array_state)
            return array_state.value

        elif token_type == JsonTokenType.ObjectStart:
            object_state = _InObjectExpectingKeyState()
            self._state_stack.append(object_state)
            return object_state.value

        else:
            raise ValueError(
                f'Unexpected token type: {json_token_type_to_string(token_type)}'
            )
