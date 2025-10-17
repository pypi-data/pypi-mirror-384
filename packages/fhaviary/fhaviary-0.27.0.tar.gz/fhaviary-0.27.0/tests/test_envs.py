import asyncio
import json
import pathlib
import re
import tempfile
import time
from collections.abc import Sequence
from typing import ClassVar

import litellm
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ValidationError
from pytest_subtests import SubTests

from aviary.core import (
    DummyEnv,
    DummyEnvState,
    Environment,
    Frame,
    Message,
    Renderer,
    TaskDataset,
    Tool,
    ToolCall,
    ToolRequestMessage,
    ToolResponseMessage,
    ToolsAdapter,
    ToolSelector,
    ToolSelectorLedger,
)
from aviary.dataset_server import TaskDatasetServer
from aviary.message import MalformedMessageError
from aviary.tools import FunctionInfo, Messages
from tests import CILLMModelNames
from tests.conftest import VCR_DEFAULT_MATCH_ON

# Mistral API v0.0.2 required tool calls to comply with this pattern
MISTRAL_API_TOOL_CALL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{9}$")


class TestDummyEnv:
    @pytest.mark.asyncio
    async def test_dummyenv(self, dummy_env: DummyEnv) -> None:
        async def my_policy(obs: list[Message]) -> ToolRequestMessage:  # noqa: ARG001, RUF029
            # For testing purposes, we hardcoded the policy
            return ToolRequestMessage(
                tool_calls=[
                    ToolCall.from_name("print_story", story="Once upon a time done")
                ],
            )

        assert isinstance(await dummy_env.get_id(), str), (
            "Expected getting ID to work before reset"
        )

        obs, _ = await dummy_env.reset()
        assert isinstance(obs, list)
        assert len(obs) == 1

        # Check if we have a bad policy that gives an empty action, the env reports this
        obs, reward, done, _ = await dummy_env.step(
            action=ToolRequestMessage(tool_calls=[])
        )
        assert not done, "Should not be done after empty action"
        assert obs[0].content
        assert "no tool calls" in obs[0].content.lower()

        action = await my_policy(obs)
        _, reward, done, _ = await dummy_env.step(action)
        assert reward > 0
        assert done

    @pytest.mark.asyncio
    async def test_tool_signatures(self, dummy_env: DummyEnv) -> None:
        _, tools = await dummy_env.reset()
        # Also check we can serialize a Tool that has null parameters
        tools.append(
            Tool(info=FunctionInfo(name="stub", description="Stub.", parameters=None))
        )
        assert ToolsAdapter.dump_python(tools, exclude_none=True) == [
            {
                "type": "function",
                "info": {
                    "name": "print_story",
                    "description": "Print a story.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "story": {
                                "type": "string",
                                "title": "Story",
                                "description": "Story to print.",
                            }
                        },
                        "required": ["story"],
                    },
                },
            },
            {
                "info": {
                    "description": "Cast the input argument x to a float.",
                    "name": "cast_float",
                    "parameters": {
                        "properties": {"x": {"type": "string", "title": "X"}},
                        "required": ["x"],
                        "type": "object",
                    },
                },
                "type": "function",
            },
            {
                "info": {
                    "description": "Cast the input argument x to an integer.",
                    "name": "cast_int",
                    "parameters": {
                        "properties": {"x": {"type": "number", "title": "X"}},
                        "required": ["x"],
                        "type": "object",
                    },
                },
                "type": "function",
            },
            {
                "type": "function",
                "info": {
                    "name": "get_random_int",
                    "description": "Get a random integer in 1 to 10.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {"type": "function", "info": {"name": "stub", "description": "Stub."}},
        ]

    def test_loading_from_name(self):
        env: DummyEnv = Environment.from_name("dummy")  # type: ignore[assignment]
        assert isinstance(env, DummyEnv)

        dataset = TaskDataset.from_name("dummy")
        batch = next(iter(dataset.iter_batches(1)))
        assert len(batch) == 1
        assert isinstance(batch[0], DummyEnv)

    @pytest.mark.parametrize(
        "model_name", [CILLMModelNames.OPENAI.value, CILLMModelNames.ANTHROPIC.value]
    )
    @pytest.mark.asyncio
    async def test_tool_calling(self, dummy_env: DummyEnv, model_name: str) -> None:
        def get_todo_list(n: int) -> str:
            """Get todo list for today.

            Args:
                n: number of items to return
            """
            return "\n".join(["Go for a walk", "Read a book", "Call a friend"][:n])

        tool = Tool.from_function(get_todo_list)
        dummy_env.tools = [tool]
        tool_request_message = ToolRequestMessage(
            tool_calls=[ToolCall.from_name("get_todo_list", n=3)]
        )
        assert all(
            MISTRAL_API_TOOL_CALL_ID_PATTERN.match(tc.id)
            for tc in tool_request_message.tool_calls
        )
        new_messages = await dummy_env.exec_tool_calls(tool_request_message)
        (new_message,) = new_messages
        assert new_message.content == "Go for a walk\nRead a book\nCall a friend"
        assert new_message.tool_call_id == tool_request_message.tool_calls[0].id

        def get_todo_list_no_args() -> str:
            """Get todo list for today."""
            return "\n".join(["Go for a walk", "Read a book", "Call a friend"])

        tool = Tool.from_function(get_todo_list_no_args)
        dummy_env.tools = [tool]
        tool_request_message = ToolRequestMessage(
            tool_calls=[ToolCall.from_name("get_todo_list_no_args")]
        )
        assert all(
            MISTRAL_API_TOOL_CALL_ID_PATTERN.match(tc.id)
            for tc in tool_request_message.tool_calls
        )
        new_messages = await dummy_env.exec_tool_calls(tool_request_message)
        (new_message,) = new_messages
        assert new_message.content == "Go for a walk\nRead a book\nCall a friend"
        assert new_message.tool_call_id == tool_request_message.tool_calls[0].id

        # ok now try with multiple functions

        def get_calendar() -> str:
            """Get text version of calendar for today."""
            return "9:00am Wake-up\n10:00pm Go to bed\n"

        tool2 = Tool.from_function(get_calendar)
        dummy_env.tools = [tool, tool2]
        tool_request_message = ToolRequestMessage(
            # NOTE: use from_tool to test coverage of that classmethod too
            tool_calls=[ToolCall.from_tool(tool), ToolCall.from_tool(tool2)],
        )
        assert all(
            MISTRAL_API_TOOL_CALL_ID_PATTERN.match(tc.id)
            for tc in tool_request_message.tool_calls
        )
        new_messages = await dummy_env.exec_tool_calls(tool_request_message)
        if model_name.startswith("claude"):
            # Anthropic not always so smart
            assert 1 <= len(new_messages) <= 2
        else:
            assert len(new_messages) == 2


@pytest.mark.asyncio
async def test_multiple_calls(dummy_env: DummyEnv) -> None:
    obs, tools = await dummy_env.reset()
    calls = [
        ToolCall.from_name(tools[0].info.name, story="Hello, how are you?"),
        ToolCall.from_name(tools[0].info.name, story="Hello, how are you?"),
        ToolCall.from_name(tools[0].info.name, story="Hello, how are you?"),
    ]
    action = ToolRequestMessage(tool_calls=calls)
    obs, reward, done, truncated = await dummy_env.step(action)
    assert reward > 0
    assert done


@pytest.mark.parametrize("concurrent_tool_calls", [False, True])
@pytest.mark.asyncio
async def test_invalid_tool_call(
    dummy_env: DummyEnv, concurrent_tool_calls: bool
) -> None:
    def sleep(duration: float) -> None:
        """Sleep for the input duration in seconds."""
        time.sleep(duration)

    sleep_tool = Tool.from_function(sleep, allow_empty_param_descriptions=True)
    _, tools = await dummy_env.reset()
    dummy_env.tools.append(sleep_tool)
    dummy_env.concurrent_tool_calls = concurrent_tool_calls

    obs, *_ = await dummy_env.step(
        ToolRequestMessage(tool_calls=[ToolCall.from_name("invalid_tool")])
    )
    assert obs
    assert obs[0].content
    assert "Invalid tool call" in obs[0].content

    # check that order is preserved even with invalid tool calls
    tool_calls = [
        ToolCall.from_tool(sleep_tool, duration=0.1),
        ToolCall.from_name("invalid_tool"),
        ToolCall.from_name("invalid_tool"),
        ToolCall.from_tool(sleep_tool, duration=0.1),
    ]
    tic = time.perf_counter()
    obs, *_ = await dummy_env.step(ToolRequestMessage(tool_calls=tool_calls))
    if concurrent_tool_calls:
        assert time.perf_counter() - tic < 0.15
    else:
        assert time.perf_counter() - tic > 0.15
    assert obs
    for o, t in zip(obs, tool_calls, strict=True):
        assert isinstance(o, ToolResponseMessage)
        assert o.tool_call_id == t.id


class SlowEnv(Environment[None]):
    async def reset(self) -> tuple[list[Message], list[Tool]]:
        async def aslow_tool() -> None:
            """I am very slow."""
            await asyncio.sleep(0.1)

        def slow_tool() -> None:
            """I am very slow."""
            time.sleep(0.1)

        self.tools = [Tool.from_function(slow_tool), Tool.from_function(aslow_tool)]
        return [], self.tools

    async def step(
        self, action: ToolRequestMessage
    ) -> tuple[Messages, float, bool, bool]:
        await self.exec_tool_calls(action, exec_timeout=0.0001)

        return [], 0.0, False, False


@pytest.mark.asyncio
async def test_tool_exec_timeout() -> None:
    env = SlowEnv()
    _, tools = await env.reset()

    for tool in tools:
        action = ToolRequestMessage(tool_calls=[ToolCall.from_tool(tool)])
        with pytest.raises(asyncio.TimeoutError):
            await env.step(action)


class TestRendering:
    class SomeState(BaseModel):
        field: int

    @pytest.mark.parametrize(
        ("state", "serialized"),
        [
            (5, 5),
            (5.6, 5.6),
            ("hi", "hi"),
            (True, True),
            (["hi"], ["hi"]),
            ({"hi": 5}, {"hi": 5}),
            (SomeState(field=5), {"field": 5}),
            (None, None),
        ],
    )
    def test_serialization(self, state, serialized) -> None:
        assert Frame(state=state).model_dump()["state"] == serialized

    def test_frame_mutability(self) -> None:
        # make a nested list - so shallow copy won't catch it
        mutable_state = [["foo"]]
        non_deep_copy = Frame(state=mutable_state, deepcopy=False)
        mutable_state[0].append("bar")
        assert non_deep_copy.model_dump()["state"] == [["foo", "bar"]]

        mutable_state = [["foo"]]
        deep_copy = Frame(state=mutable_state)
        mutable_state[0].append("bar")
        assert deep_copy.model_dump()["state"] == [["foo"]]

    def test_rendering(self, dummy_env: DummyEnv, subtests: SubTests) -> None:
        # Reset to add state
        asyncio.run(dummy_env.reset())
        frame_after_reset = dummy_env.export_frame()

        renderer = Renderer(name="Name", prefix="test")
        renderer.append(frame_after_reset)
        with subtests.test(msg="check-can-deduplicate-frames"):
            assert frame_after_reset in renderer.frames, (
                "Should be able to not add duplicate Frames to the renderer"
            )

        with (
            subtests.test(msg="build-rehydrate"),
            tempfile.TemporaryDirectory() as tmpdir,
        ):
            build_dir = pathlib.Path(tmpdir)
            renderer.build(build_dir)
            file_paths = list(build_dir.glob("*.json"))
            assert len(file_paths) == 2, "Expected manifest and one object"
            frame_path = file_paths[
                file_paths[0].name.removeprefix("test_").startswith("info")
            ]
            with frame_path.open() as f:
                rehydrated = json.load(f)
            assert rehydrated["state"]["messages"] == [
                "Write a 5 word story via print_story about applesauce"
            ]


class ParallelizedDummyEnv(DummyEnv):
    def __init__(self, right_hand_broken: bool = False):
        super().__init__()
        self.right_hand_broken = right_hand_broken

    RIGHT_HAND_BROKEN_MESSAGE: ClassVar[str] = "Right hand is broken."

    async def reset(self) -> tuple[list[Message], list[Tool]]:
        def move_right_hand(
            distance: int,  # noqa: ARG001
            state: DummyEnvState,
        ) -> None:
            """
            Move your right hand forward or backward.

            Args:
                distance: Integer distance to move (mm), where forward is positive.
                state: Current state.
            """
            if self.right_hand_broken:  # Use this to test tool errors
                raise RuntimeError(self.RIGHT_HAND_BROKEN_MESSAGE)
            state.reward += 1

        def move_left_hand(
            distance: int,  # noqa: ARG001
            state: DummyEnvState,
        ) -> None:
            """
            Move your left hand forward or backward.

            Args:
                distance: Integer distance to move (mm), where forward is positive.
                state: Current state.
            """
            state.reward += 1

        def smile_and_wave(state: DummyEnvState) -> None:
            """
            Smile and wave.

            Args:
                state: Current state.
            """
            state.reward = 10
            state.done = True

        self.tools = [
            Tool.from_function(move_left_hand),
            Tool.from_function(move_right_hand),
            Tool.from_function(smile_and_wave),
        ]
        self.state = type(self).State(
            messages=[
                Message(
                    role="user",
                    content=(
                        "You are the president of the United States of America."
                        " Please move both hands at the same time, and then smile"
                        " and wave."
                    ),
                )
            ]
        )
        return self.state.messages, self.tools


class TestParallelism:
    @pytest.mark.parametrize(
        "model_name", [CILLMModelNames.ANTHROPIC.value, "gpt-4-turbo"]
    )
    @pytest.mark.asyncio
    async def test_exec_tool_calls_handling(self, model_name: str) -> None:
        env = ParallelizedDummyEnv(right_hand_broken=True)
        obs: Sequence[Message]
        obs, tools = await env.reset()
        right_hand_tool = tools[1]

        # 1. Let's DIY create a ToolRequestMessage for test determinism
        request_msg = ToolRequestMessage(
            tool_calls=[ToolCall.from_tool(right_hand_tool, distance=5)]
        )

        # 2. Okay, our hand was broken, let's handle it DIY-style
        try:
            obs, *_ = await env.step(action=request_msg)
        except RuntimeError as exc:
            obs = [
                Message(
                    content=f"Failed to execute tools with message:\n{exc}", role="tool"
                )
            ]
        else:
            raise AssertionError("Should have blown up per the test logic.")

        # 2. Now that we have confirmed that, let's make sure exec_tool_calls
        #    can automate this for us
        obs = await env.exec_tool_calls(
            message=request_msg, state=env.state, handle_tool_exc=True
        )
        (failure_tool_response,) = obs
        assert isinstance(failure_tool_response, ToolResponseMessage)
        assert env.RIGHT_HAND_BROKEN_MESSAGE in failure_tool_response.content

        # 3. Let's check how the string formatting works for ExceptionGroup
        async def dance(style: str) -> None:  # noqa: ARG001
            """Dance in a given style."""

            async def inner1() -> None:  # noqa: RUF029
                """Inner function that raises an Exception."""
                raise RuntimeError("BOOM, blew out an ACL.")

            async with asyncio.TaskGroup() as tg:  # Leads to ExceptionGroup
                _ = tg.create_task(inner1())

        dance_tool = Tool.from_function(dance, allow_empty_param_descriptions=True)
        env.tools.append(dance_tool)
        (tool_response_msg,) = await env.exec_tool_calls(
            ToolRequestMessage(
                tool_calls=[ToolCall.from_tool(dance_tool, style="salsa")]
            ),
            handle_tool_exc=True,
        )
        assert "BOOM" in tool_response_msg.content, (
            "Expected sub-exceptions to be displayed"
        )

    @pytest.mark.asyncio
    async def test_tool_selector_bad_agent_llm_response(
        self, dummy_env: DummyEnv
    ) -> None:
        obs, tools = await dummy_env.reset()

        async def stub_acompletion(*_, **__) -> litellm.ModelResponse:  # noqa: RUF029
            return litellm.ModelResponse(
                choices=[
                    litellm.Choices(
                        # Malformatted because it contains null tool calls
                        message=ToolRequestMessage().model_dump() | {"tool_calls": None}
                    )
                ]
            )

        selector = ToolSelector("stub", acompletion=stub_acompletion)
        with pytest.raises(
            MalformedMessageError, match="tool request message"
        ) as exc_info:
            await selector(obs, tools=tools)
        assert isinstance(exc_info.value.__cause__, ValidationError), (
            "We should be able to retrieve the original validation error"
        )

    @pytest.mark.vcr(match_on=[*VCR_DEFAULT_MATCH_ON, "body"])
    @pytest.mark.parametrize("model_name", [CILLMModelNames.OPENAI.value])
    @pytest.mark.asyncio
    async def test_tool_selector_from_model_name(
        self, subtests: SubTests, model_name: str
    ) -> None:
        env = ParallelizedDummyEnv()
        obs, tools = await env.reset()

        with subtests.test("'required' tool_choice"):
            ledger = ToolSelectorLedger(tools=tools)
            selector = ToolSelector(model_name)
            tool_request_message = await selector(obs, tools)
            ledger.messages.append(tool_request_message)
            ledger.model_dump()  # Proving we can serialize the ledger
            assert isinstance(tool_request_message, ToolRequestMessage)
            assert tool_request_message.tool_calls, "Expected at least one tool call"

        with subtests.test("'auto' tool_choice"):
            # NOTE: 'auto' can work, but you risk the ToolSelector not actually
            # selecting a tool, which is why 'auto' is not the default
            ledger = ToolSelectorLedger(tools=tools)
            selector = ToolSelector(model_name)
            tool_request_message = await selector(obs, tools, tool_choice="auto")
            ledger.messages.append(tool_request_message)
            ledger.model_dump()  # Proving we can serialize the ledger
            assert isinstance(tool_request_message, ToolRequestMessage)
            assert tool_request_message.tool_calls, "Expected at least one tool call"

    @pytest.mark.vcr
    @pytest.mark.parametrize("model_name", [CILLMModelNames.OPENAI.value])
    @pytest.mark.asyncio
    async def test_tool_selector_with_external_acompletion(
        self, model_name: str
    ) -> None:
        env = ParallelizedDummyEnv()
        obs_tools = await env.reset()

        router = litellm.Router(
            model_list=[
                litellm.DeploymentTypedDict(
                    model_name="openai", litellm_params={"model": model_name}
                )
            ]
        )
        selector = ToolSelector("openai", router.acompletion)
        tool_request_message = await selector(*obs_tools)
        assert isinstance(tool_request_message, ToolRequestMessage)
        assert tool_request_message.tool_calls, "Expected at least one tool call"

        assert tool_request_message.info, "Expected message info"
        assert tool_request_message.info["usage"][0] > 0, "Expected prompt tokens"
        assert tool_request_message.info["model"], "Expected model name"

    @pytest.mark.vcr(match_on=[*VCR_DEFAULT_MATCH_ON, "body"])
    @pytest.mark.asyncio
    async def test_dummyenv_using_empty_params(self, dummy_env: DummyEnv) -> None:
        _, tools = await dummy_env.reset()  # Populate tools

        # Let's use a tool that has no parameters for the objective
        obs = [Message(content="Please get a random integer.")]
        expected_tool_call_fn = ToolCall.from_tool(tools[-1]).function
        dummy_env.state = dummy_env.State(messages=obs)

        selector = ToolSelector("gemini/gemini-1.5-flash")

        assert any(not t.info.get_properties() for t in tools), (
            "Test requires empty properties"
        )
        tool_request_message = await selector(messages=obs, tools=tools)
        assert [tc.function for tc in tool_request_message.tool_calls] == [
            expected_tool_call_fn
        ]


@pytest.fixture
def server_async_client() -> AsyncClient:
    dataset = TaskDataset.from_name("dummy")
    server = TaskDatasetServer[DummyEnv](dataset)
    # Use httpx.AsyncClient over httpx_aiohttp.HttpxAiohttpClient in tests here,
    # as httpx_aiohttp.AiohttpTransport doesn't support an app argument
    # as of httpx-aiohttp==0.1.8
    return AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test")


class TestTaskDatasetServer:
    @pytest.mark.asyncio
    async def test_start(self, server_async_client: AsyncClient):
        response = await server_async_client.post("/start", json={})
        assert response.status_code == 200
        assert "env_id" in response.json()

    @pytest.mark.asyncio
    async def test_reset_and_step(self, server_async_client: AsyncClient):
        # First, start a new environment
        start_resp = await server_async_client.post("/start", json={})
        env_id = start_resp.json()["env_id"]

        # Now, reset the environment
        response = await server_async_client.post("/reset", json={"env_id": env_id})
        assert response.status_code == 200
        obs, tools = response.json()
        assert isinstance(obs, list)
        assert isinstance(tools, list)

        # Define an action
        action = ToolRequestMessage(
            tool_calls=[
                ToolCall.from_name("print_story", story="Once upon a time done")
            ]
        )

        # Perform a step
        response = await server_async_client.post(
            "/step", json={"env_id": env_id, "action": action.model_dump()}
        )
        assert response.status_code == 200
        obs, reward, done, truncated = response.json()
        assert isinstance(obs, list)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(truncated, bool)

    @pytest.mark.asyncio
    async def test_close(self, server_async_client: AsyncClient):
        # Start a new environment
        start_resp = await server_async_client.post("/start", json={})
        env_id = start_resp.json()["env_id"]

        # Close the environment
        response = await server_async_client.post("/close", json={"env_id": env_id})
        assert response.status_code == 200
        assert response.json()["env_id"] == env_id

    @pytest.mark.asyncio
    async def test_close_old_envs(self, server_async_client: AsyncClient):
        # Start a new environment
        await server_async_client.post("/start", json={})

        # Close environments not used in the last 0 seconds
        response = await server_async_client.post(
            "/close_old_envs", json={"last_used": 0}
        )
        assert response.status_code == 200
        assert "closed_env_ids" in response.json()

    @pytest.mark.asyncio
    async def test_info(self, server_async_client: AsyncClient):
        response = await server_async_client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data == {
            "dataset_size": None,
            "running_env_ids": [],
        }
