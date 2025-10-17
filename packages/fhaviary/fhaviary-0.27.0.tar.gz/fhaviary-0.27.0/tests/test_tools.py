import asyncio
import json
import os
import pickle
from collections.abc import Callable, Sequence
from enum import IntEnum, auto
from typing import Any, cast
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from pytest_subtests import SubTests
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from typeguard import suppress_type_checks

from aviary.core import (
    INVALID_TOOL_NAME,
    DummyEnv,
    Environment,
    FunctionInfo,
    Message,
    Tool,
    ToolCall,
    ToolRequestMessage,
    argref_by_name,
)
from aviary.tools.server import make_tool_server


def simple() -> None:
    """Doing nothing may be better than doing something."""


def intuitive_arg(x: str) -> float:  # type: ignore[empty-body]
    """Cast the input argument x to a float."""


class StubState(BaseModel):
    """Stub model docstring."""

    defaulted_int: int = Field(default=1, description="A description of the int.")
    required_str: str = Field(description="A description of the str.")


class StubEnum(IntEnum):
    """Stub enum docstring."""

    STUB1 = auto()
    STUB2 = auto()


def many_edge_cases(
    x: int,
    y: None,
    union: int | None,
    pydantic_model: StubState,
    basic_dict: dict[str, int],
    complex_dict: dict[str, tuple[str, int]],
    enum: StubEnum,
    defaulted_str: str = "default",
    defaulted_float: float = 1.0,
    structured_arg: str = "structured",
) -> None:
    """
    Check using docstrings as partial f-string templates like so: {summary_format}.

    Args:
        x: Yes, I end with a colon :
        y: I am null.
            And despite that there is a multiline argument description.
        union: I am a union and the current year is {current_year}.
        pydantic_model: I am a Pydantic model.
        basic_dict: I am a dictionary with primitive values.
        complex_dict: I am a dictionary with complex values.
        enum: I am an enum.
        defaulted_str: I have a string default value.
        defaulted_float: I have a float default value.
        structured_arg: I am structured. There are lots of examples
            included which cross several lines.
            Query Syntax:
                Basic Search:
                    Search with two words and a space:
                    >>> "word1 word2"  # doctest: +SKIP

                Modified Search:
                    Use operators to modify search behavior:
                    >>> 'EXPANSION[None]NAME"word phrase"'  # doctest: +SKIP
                    >>> 'EXPANSION[Concept]"words"'  # doctest: +SKIP

            Operators:
                EXPANSION[type]: Terms
                    - Term1: a description
                    - Term2: another description
    """


def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: first number
        b: second number

    Returns:
        I am not yet included, perhaps someday I should be.
    """
    return a + b


def example_fxn(x: int, y: str, z: float) -> None:
    r"""A test function.

    There may be non-summary content.

    \f

    I should be ignored.

    Args:
        x: x
        y: y
        z: z
    """
    assert isinstance(x, int)
    assert isinstance(y, str)
    assert isinstance(z, float)


def state_out_of_order(state: dict, x: int = 0) -> None:
    """A test function.

    There may be non-summary content.

    Args:
        state: this should not be present
        x: x
    """
    assert isinstance(state, dict)
    assert isinstance(x, int)


@retry(retry=retry_if_exception_type(ValueError), stop=stop_after_attempt(3))
def add_with_tenacity_retries(a: int, b: int | None = 0) -> int:
    """Add two numbers.

    Args:
        a: first number
        b: second number
    """
    if b is None:
        # Intentionally don't use ValueError since we don't want to trigger retries
        raise TypeError("Please pass b as a number.")
    return a + b


class TestTool:
    @pytest.mark.parametrize(
        ("fn", "kwargs", "expected"),
        [
            pytest.param(
                simple,
                {},
                {
                    "type": "function",
                    "info": {
                        "name": "simple",
                        "description": (
                            "Doing nothing may be better than doing something."
                        ),
                        "parameters": {
                            "properties": {},
                            "required": [],
                            "type": "object",
                        },
                    },
                },
                id="only-summary",
            ),
            pytest.param(
                intuitive_arg,
                {"allow_empty_param_descriptions": True},
                {
                    "type": "function",
                    "info": {
                        "name": "intuitive_arg",
                        "description": "Cast the input argument x to a float.",
                        "parameters": {
                            "properties": {"x": {"title": "X", "type": "string"}},
                            "required": ["x"],
                            "type": "object",
                        },
                    },
                },
                id="only-summary",
            ),
            pytest.param(
                many_edge_cases,
                {"current_year": 2024},  # Intentionally left format_1 unformatted,
                {
                    "type": "function",
                    "info": {
                        "name": "many_edge_cases",
                        "description": (
                            "Check using docstrings as partial f-string templates like"
                            " so: {summary_format}."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "description": "Yes, I end with a colon :",
                                    "title": "X",
                                    "type": "integer",
                                },
                                "y": {
                                    "description": (
                                        "I am null.\nAnd despite that there is a"
                                        " multiline argument description."
                                    ),
                                    "title": "Y",
                                    "type": "null",
                                },
                                "union": {
                                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                                    "description": (
                                        "I am a union and the current year is 2024."
                                    ),
                                    "title": "Union",
                                },
                                "pydantic_model": {
                                    "$ref": "#/$defs/StubState",
                                    "description": "I am a Pydantic model.",
                                },
                                "basic_dict": {
                                    "additionalProperties": {"type": "integer"},
                                    "description": (
                                        "I am a dictionary with primitive values."
                                    ),
                                    "title": "Basic Dict",
                                    "type": "object",
                                },
                                "complex_dict": {
                                    "additionalProperties": {
                                        "maxItems": 2,
                                        "minItems": 2,
                                        "prefixItems": [
                                            {"type": "string"},
                                            {"type": "integer"},
                                        ],
                                        "type": "array",
                                    },
                                    "description": (
                                        "I am a dictionary with complex values."
                                    ),
                                    "title": "Complex Dict",
                                    "type": "object",
                                },
                                "enum": {
                                    "$ref": "#/$defs/StubEnum",
                                    "description": "I am an enum.",
                                },
                                "defaulted_str": {
                                    "default": "default",
                                    "description": "I have a string default value.",
                                    "title": "Defaulted Str",
                                    "type": "string",
                                },
                                "defaulted_float": {
                                    "default": 1.0,
                                    "description": "I have a float default value.",
                                    "title": "Defaulted Float",
                                    "type": "number",
                                },
                                "structured_arg": {
                                    "default": "structured",
                                    "description": (
                                        "I am structured. There are lots of examples\n"
                                        "included which cross several lines.\n"
                                        "Query Syntax:\n"
                                        "    Basic Search:\n"
                                        "        Search with two words and a space:\n"
                                        '        >>> "word1 word2"  # doctest: +SKIP\n'
                                        "\n"
                                        "    Modified Search:\n"
                                        "        Use operators to modify search behavior:\n"
                                        "        >>> 'EXPANSION[None]NAME\"word phrase\"'  # doctest: +SKIP\n"
                                        "        >>> 'EXPANSION[Concept]\"words\"'  # doctest: +SKIP\n"
                                        "\n"
                                        "Operators:\n"
                                        "    EXPANSION[type]: Terms\n"
                                        "        - Term1: a description\n"
                                        "        - Term2: another description"
                                    ),
                                    "title": "Structured Arg",
                                    "type": "string",
                                },
                            },
                            "required": [
                                "x",
                                "y",
                                "union",
                                "pydantic_model",
                                "basic_dict",
                                "complex_dict",
                                "enum",
                            ],
                            "$defs": {
                                "StubEnum": {
                                    "description": "Stub enum docstring.",
                                    "enum": [1, 2],
                                    "title": "StubEnum",
                                    "type": "integer",
                                },
                                "StubState": {
                                    "description": "Stub model docstring.",
                                    "properties": {
                                        "defaulted_int": {
                                            "default": 1,
                                            "description": "A description of the int.",
                                            "title": "Defaulted Int",
                                            "type": "integer",
                                        },
                                        "required_str": {
                                            "description": "A description of the str.",
                                            "title": "Required Str",
                                            "type": "string",
                                        },
                                    },
                                    "required": ["required_str"],
                                    "title": "StubState",
                                    "type": "object",
                                },
                            },
                        },
                    },
                },
                id="many-edge-cases",
            ),
            pytest.param(
                add,
                {},
                {
                    "type": "function",
                    "info": {
                        "name": "add",
                        "description": "Add two numbers.",
                        "parameters": {
                            "properties": {
                                "a": {
                                    "description": "first number",
                                    "title": "A",
                                    "type": "integer",
                                },
                                "b": {
                                    "description": "second number",
                                    "title": "B",
                                    "type": "integer",
                                },
                            },
                            "required": ["a", "b"],
                            "type": "object",
                        },
                    },
                },
                id="with-args-and-returns",
            ),
            pytest.param(
                state_out_of_order,
                {},
                {
                    "type": "function",
                    "info": {
                        "name": "state_out_of_order",
                        "description": (
                            "A test function.\n\nThere may be non-summary content."
                        ),
                        "parameters": {
                            "properties": {
                                "x": {
                                    "default": 0,
                                    "description": "x",
                                    "title": "X",
                                    "type": "integer",
                                },
                            },
                            "required": [],
                            "type": "object",
                        },
                    },
                },
                id="with-state-out-of-order",
            ),
            pytest.param(
                example_fxn,
                {},
                {
                    "type": "function",
                    "info": {
                        "name": "example_fxn",
                        "description": (
                            "A test function.\n\nThere may be non-summary content."
                        ),
                        "parameters": {
                            "properties": {
                                "x": {
                                    "description": "x",
                                    "title": "X",
                                    "type": "integer",
                                },
                                "y": {
                                    "description": "y",
                                    "title": "Y",
                                    "type": "string",
                                },
                                "z": {
                                    "description": "z",
                                    "title": "Z",
                                    "type": "number",
                                },
                            },
                            "required": ["x", "y", "z"],
                            "type": "object",
                        },
                    },
                },
                id="with-linefeed",
            ),
            pytest.param(
                # NOTE: tenacity uses `functools.wraps`: https://github.com/jd/tenacity/blob/9.1.2/tenacity/__init__.py#L330-L333
                # Also, we commonly use `tenacity.retry`, so it's useful to check this too
                add_with_tenacity_retries,
                {},
                {
                    "type": "function",
                    "info": {
                        "name": "add_with_tenacity_retries",
                        "description": "Add two numbers.",
                        "parameters": {
                            "properties": {
                                "a": {
                                    "description": "first number",
                                    "title": "A",
                                    "type": "integer",
                                },
                                "b": {
                                    "description": "second number",
                                    "title": "B",
                                    "default": 0,
                                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                                },
                            },
                            "required": ["a"],
                            "type": "object",
                        },
                    },
                },
                id="functools-wraps-decoration",
            ),
        ],
    )
    def test_from_function(
        self, fn: Callable, kwargs: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        assert (
            Tool.from_function(fn, **kwargs).model_dump(exclude_none=True) == expected
        )

    @pytest.mark.parametrize(
        ("fn", "kwargs", "expected"),
        [
            (
                example_fxn,
                {},
                """NAME: example_fxn

SYNOPSIS:
    example_fxn(integer x, string y, number z)

DESCRIPTION:
    A test function.

    There may be non-summary content.

PARAMETERS:
    x (integer): x
    y (string): y
    z (number): z""",
            ),
            (
                intuitive_arg,
                {"allow_empty_param_descriptions": True},
                """NAME: intuitive_arg

SYNOPSIS:
    intuitive_arg(string x)

DESCRIPTION:
    Cast the input argument x to a float.

PARAMETERS:
    x (string): No description provided.""",
            ),
        ],
    )
    def test_describe_str(
        self, fn: Callable, kwargs: dict[str, Any], expected: str
    ) -> None:
        tool = Tool.from_function(fn, **kwargs)
        assert tool.info.describe_str().strip() == expected

    def test_describe(self, subtests: SubTests) -> None:
        """Test that describe_xyz functions for FunctionInfo are reasonable."""
        tool = Tool.from_function(many_edge_cases)

        with subtests.test("Test describe_xml is callable"):
            assert tool.info.describe_xml()

        with subtests.test("Test describe_json is callable"):
            assert tool.info.describe_json()

        with subtests.test("Test describe_str is callable"):
            assert tool.info.describe_str()

    def test_serialization_manual(self) -> None:
        # make one manually
        tool = Tool(
            tool_fn=add,
            info=FunctionInfo(
                name="add",
                description="Add two numbers.",
                parameters={
                    "properties": {
                        "a": {
                            "description": "first number",
                            "title": "A",
                            "type": "integer",
                        },
                        "b": {
                            "description": "second number",
                            "title": "B",
                            "type": "integer",
                        },
                    },
                    "required": ["a", "b"],
                    "type": "object",
                },
            ),
        )

        ref = json.loads(r"""{
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "integer",
                        "title": "A",
                        "description": "first number"
                    },
                    "b": {
                        "type": "integer",
                        "title": "B",
                        "description": "second number"
                    }
                },
                "required": [
                    "a",
                    "b"
                ]
            }
        }
    }""")
        # make sure it agrees with the reference
        my_dump = json.loads(tool.model_dump_json(exclude_none=True, by_alias=True))
        assert my_dump == ref

        # make one from a function
        tool_fxn = Tool.from_function(add)
        # make sure it serializes correctly
        assert tool_fxn.model_dump_json(
            exclude_none=True, by_alias=True
        ) == tool.model_dump_json(exclude_none=True, by_alias=True)

    @pytest.mark.asyncio
    async def test_arg_types(self) -> None:
        tool = Tool.from_function(example_fxn)

        assert tool.info.parameters is not None
        assert tool.info.parameters.properties["x"]["type"] == "integer"
        assert tool.info.parameters.properties["y"]["type"] == "string"
        assert tool.info.parameters.properties["z"]["type"] == "number"

        calls = [
            ToolCall.from_name(tool.info.name, x=5, y="hi", z=4.2),
        ]
        for call in calls:
            # Call the function to make sure argument types
            # are passed correctly. Private because
            # it doesn't serialize
            tool._tool_fn(**call.function.arguments)

    @pytest.mark.asyncio
    async def test_tool_serialization(
        self, dummy_env: DummyEnv, subtests: SubTests
    ) -> None:
        def get_todo_list(n: int):
            """Get todo list for today.

            Args:
                n: number of items to return
            """
            return "\n".join(["Go for a walk", "Read a book", "Call a friend"][:n])

        tool = Tool.from_function(get_todo_list)

        with subtests.test("pickling"):
            # Check round-trip pickling doesn't break the original Tool
            orig_tool_fn_id = id(tool._tool_fn)
            pickle.loads(pickle.dumps(tool))  # noqa: S301
            assert id(tool._tool_fn) == orig_tool_fn_id

        with subtests.test("serialization then deserialization"):
            tool_copy = Tool(**tool.model_dump(by_alias=True))
            assert tool.type == tool_copy.type
            assert tool.info == tool_copy.info

        dummy_env.tools = [tool]

        with subtests.test("tool call from dump"):
            # Mimic the way an ToolCall might be invoked by an LLM API:
            # the arguments will be strings.
            action = ToolRequestMessage(**{  # noqa: PIE804
                "tool_calls": [
                    {
                        "id": "good_tool_call",
                        "function": {"name": "get_todo_list", "arguments": '{"n": 2}'},
                    },
                    {
                        "id": "bad_tool_call",
                        "function": {
                            "name": "get_todo_list",
                            "arguments": '({"n": 2})',  # NOTE: invalid JSON
                        },
                    },
                ]
            })

            assert action.tool_calls[0].function.arguments == {"n": 2}
            assert action.tool_calls[1].function.name == INVALID_TOOL_NAME

        with subtests.test("tool call from name"):
            tool_call = ToolCall.from_name("get_todo_list", n=2)
            action = ToolRequestMessage(tool_calls=[tool_call])
            new_messages = await dummy_env.exec_tool_calls(action)
            assert new_messages[0].content == "Go for a walk\nRead a book"

        with subtests.test("tool call from tool"):
            tool_call = ToolCall.from_tool(tool, n=2)
            action = ToolRequestMessage(tool_calls=[tool_call])
            new_messages = await dummy_env.exec_tool_calls(action)
            assert new_messages[0].content == "Go for a walk\nRead a book"

        with subtests.test("tool call from tool with no kwargs"):
            tool_call = ToolCall.from_tool(tool, 3)
            action = ToolRequestMessage(tool_calls=[tool_call])
            new_messages = await dummy_env.exec_tool_calls(action)
            assert (
                new_messages[0].content == "Go for a walk\nRead a book\nCall a friend"
            )

        def get_todo_list_no_args():
            """Get todo list for today."""
            return "Go for a walk"

        tool = Tool.from_function(get_todo_list_no_args)
        dummy_env.tools = [tool]

        with subtests.test("tool call from tool with no args and order mismatch"):
            tool_call = ToolCall.from_tool(tool)
            action = ToolRequestMessage(tool_calls=[tool_call])
            new_messages = await dummy_env.exec_tool_calls(action)
            assert new_messages[0].content == "Go for a walk"

            tool_call = ToolCall.from_tool(tool, 1, 10, 30441)
            action = ToolRequestMessage(tool_calls=[tool_call])
            new_messages = await dummy_env.exec_tool_calls(action)
            assert new_messages[0].content == "Go for a walk"

    @pytest.mark.asyncio
    async def test_tool_timing(self) -> None:
        sleep_time = 0.1

        async def sleep_tool_fn() -> None:
            """Zzz."""
            await asyncio.sleep(sleep_time)

        tool = Tool.from_function(sleep_tool_fn)
        tool_calls = [ToolCall.from_tool(tool) for _ in range(3)]

        dummy_env = DummyEnv()
        dummy_env.tools = [tool]

        responses = await dummy_env.exec_tool_calls(
            ToolRequestMessage(tool_calls=tool_calls)
        )

        for resp in responses:
            assert resp.info, "Expected timing info to be present"
            assert resp.info["end_ts"] - resp.info["start_ts"] >= sleep_time, (
                "Expected non-trivial time elapsed."
            )


def test_argref_by_name_basic_usage() -> None:
    class MyState:
        def __init__(self):
            self.refs = {"foo": 1}

    # Check we can use argref_by_name to add 1 + 2 using a value in refs
    wrapped_add = argref_by_name(args_to_skip={"b"})(add)
    s = MyState()

    result = wrapped_add("foo", 2, state=s)
    # Now s.refs has a new entry at the below `name`
    name = result.split()[0]
    assert s.refs[name] == 1 + 2

    # Check kwargs work too
    result = wrapped_add(a="foo", b=2, state=s)
    name = result.split()[0]
    assert s.refs[name] == 1 + 2


def test_argref_by_name_error_handling() -> None:
    class MyState:
        def __init__(self):
            self.refs = {"foo": 1}

    wrapped_add = argref_by_name()(add)
    s = MyState()

    # Check if we use a key name that doesn't exist, we blow up
    with pytest.raises(KeyError, match="not found in state"):
        wrapped_add("bar", 2, state=s)

    # Check if state doesn't have refs, we blow up
    with pytest.raises(AttributeError, match="must have a 'refs' attribute"):
        wrapped_add("foo", 2, state="not a state")

    # Check that we cannot pass a direct value as a kwarg
    with pytest.raises(KeyError, match="Key is not present"):
        wrapped_add(a=1, b=2, state=s)


@pytest.mark.asyncio
async def test_argref_by_name_async_functions() -> None:
    class MyState:
        def __init__(self):
            self.refs = {"foo": 1, "bar": 7}

    # Define the async_add function with the decorator
    @argref_by_name()
    async def async_add(a: int, b: int) -> int:  # noqa: RUF029
        """Some docstring."""
        return a + b

    s = MyState()
    result = await async_add("foo", 2, state=s)
    assert s.refs[result.split()[0]] == 1 + 2

    result = await async_add(6, 2, state=s)
    assert s.refs[result.split()[0]] == 6 + 2

    # Now try with lists
    result = await async_add("foo", "bar", state=s)
    assert s.refs[result.split()[0]] == 1 + 7

    # Try the convenience of comma splitting on key
    result = await async_add("foo,bar", state=s)
    assert s.refs[result.split()[0]] == 1 + 7

    # Define and test async_list
    @argref_by_name()
    async def async_list(a: int, b: int) -> list[int]:  # noqa: RUF029
        """Some docstring."""
        return [a, b]

    result = await async_list("foo", 2, state=s)
    name1, name2 = (n.split()[0] for n in result.split("\n"))
    assert s.refs[name1] == 1
    assert s.refs[name2] == 2

    # Define and test async_list_direct
    @argref_by_name(return_direct=True)
    async def async_list_direct(a: int, b: int) -> list[int]:  # noqa: RUF029
        """Some docstring."""
        return [a, b]

    assert await async_list_direct("foo", 2, state=s) == [1, 2]


@pytest.mark.asyncio
async def test_argref_by_name_advanced_features() -> None:
    class MyState:
        def __init__(self):
            self.refs = {"foo": 1}

    s = MyState()

    # Define and test dereference via no state value found with return_direct
    @argref_by_name(return_direct=True)
    def skip_deref_test(foo: float, a: str) -> str:
        """Some docstring."""
        return f"{foo} {a}"

    assert skip_deref_test("foo", "not in state", state=s) == "1 not in state"
    assert skip_deref_test("foo", "foo", state=s) == "1 1"

    # Call in context using Tool and related classes
    wrapped_add = argref_by_name(args_to_skip={"b"})(add)
    tool = Tool.from_function(wrapped_add)

    tool_call = ToolCall.from_tool(tool, "foo", b=2)
    action = ToolRequestMessage(tool_calls=[tool_call])
    my_env = DummyEnv()
    my_env.tools = [tool]
    new_messages = await my_env.exec_tool_calls(action, state=MyState())
    assert new_messages[0].content.endswith("3")

    # Assert that we can describe the tool
    assert tool.info.describe_str()
    assert "(Pass a string key instead of the full object)" in tool.info.describe_str()

    # Test state passing with fxn_requires_state
    @argref_by_name(fxn_requires_state=True)
    async def want_state(a: int, state: MyState) -> int:  # noqa: ARG001, RUF029
        """Some docstring.

        Args:
            a: first number
            state: the state object
        """
        return 2 * a

    tool = Tool.from_function(want_state)
    action = ToolRequestMessage(tool_calls=[ToolCall.from_tool(tool, "foo")])
    my_env = DummyEnv()
    my_env.tools = [tool]
    await my_env.exec_tool_calls(action, state=MyState())

    # Check we can pass kwarg lists as comma-separated keys
    @argref_by_name(return_direct=True)
    def kwarg_list_test(a: list[int]) -> int:
        return sum(a)

    assert kwarg_list_test(a="foo,foo", state=s) == 2


def test_argref_by_name_type_checking() -> None:
    class MyInt(int):
        pass

    class MyState:
        def __init__(self):
            self.refs = {
                "int_arg": 1,
                "str_arg": "abc",
                "int_list_arg": [1],
                "str_list_arg": ["abc"],
                "my_int_list_arg": [MyInt()],
            }

    s = MyState()

    def typed_fn(a: int, b) -> int:  # noqa: ARG001
        """Some docstring."""
        return a

    # Make sure we can decorate the function twice. Decoration should not
    # modify the underlying function or its annotations.
    for _ in range(2):
        type_checked_fn = argref_by_name(type_check=True)(typed_fn)

        type_checked_fn(a="int_arg", b="str_arg", state=s)  # correctly-typed
        with pytest.raises(TypeError):
            # A non-int value is passed to a by name
            type_checked_fn(a="str_arg", b="str_arg", state=s)

    def complex_typed_fn(c: Sequence[int], d: int | str) -> None:
        """Some docstring."""

    for _ in range(2):
        type_checked_fn = argref_by_name(type_check=True)(complex_typed_fn)

        type_checked_fn(c="int_list_arg", d="str_arg", state=s)  # correctly-typed
        # list[MyInt] should match Sequence[int]
        type_checked_fn(c="my_int_list_arg", d="str_arg", state=s)

        with pytest.raises(TypeError):
            # passing int, not list[int]
            type_checked_fn(c="int_arg", d="str_arg", state=s)

        with pytest.raises(TypeError):
            # passing list[str], not list[int]
            type_checked_fn(c="str_list_arg", d="int_arg", state=s)


@pytest.mark.asyncio
async def test_make_tool_server():
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(a: int, b: int) -> int:
        """Subtract two numbers.

        Args:
            a: first number
            b: second number
        """
        return a - b

    class MyEnv(Environment):
        async def reset(self) -> tuple[list[Message], list[Tool]]:
            tools = [
                Tool.from_function(add, allow_empty_param_descriptions=True),
                Tool.from_function(subtract),
            ]
            self.tools = tools
            return [], tools

        async def step(self, action):
            return await self.exec_tool_calls(action), False, 0, 0

        async def export_frame(self):
            pass

    with suppress_type_checks():
        server = await make_tool_server(MyEnv)

    # make sure there are two endpoints
    route_names = [route.name for route in server.routes]
    assert "add" in route_names
    assert "subtract" in route_names

    # make sure we can call them
    client = TestClient(server)
    token = "stub"
    with patch.dict(os.environ, {"AUTH_TOKEN": token}):
        response = client.post(
            "/add", json={"a": 1, "b": 2}, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["result"] == "3"


@pytest.mark.asyncio
async def test_mixed_concurrency() -> None:
    # Counts the number of tools executing concurrently
    counter = 0
    counter_lock = asyncio.Lock()

    async def sleep_fn() -> int:
        """Stub."""
        nonlocal counter
        async with counter_lock:
            counter += 1
            counter_val = counter
        await asyncio.sleep(0.5)
        async with counter_lock:
            counter -= 1
        return counter_val

    async def unsafe_sleep_fn() -> int:
        """Stub."""
        return await sleep_fn()

    safe_sleep = Tool.from_function(sleep_fn)
    unsafe_sleep = Tool.from_function(unsafe_sleep_fn, concurrency_safe=False)

    dummy_env = DummyEnv()
    await dummy_env.reset()
    dummy_env.tools = [safe_sleep, unsafe_sleep]

    safes = [True, True, True, False, True, False, False, True, True]
    obs, *_ = await dummy_env.step(
        ToolRequestMessage(
            tool_calls=[
                ToolCall.from_tool(safe_sleep if safe else unsafe_sleep)
                for safe in safes
            ]
        )
    )

    at_least_one_parallel = False
    for safe, msg in zip(safes, obs, strict=True):
        count = int(cast(str, msg.content))
        if safe:
            at_least_one_parallel |= count > 1
        else:
            assert count == 1, "Expected unsafe tools to block all other tool calls."

    assert at_least_one_parallel, (
        "Expected at least one safe tool call to run concurrently with another."
    )
