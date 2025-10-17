from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Iterator
from copy import deepcopy
from typing import Annotated, ClassVar, Generic, Self, TypeAlias, TypeVar, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    ValidationInfo,
    WrapSerializer,
    field_validator,
)

from aviary.message import Message
from aviary.tools import (
    Messages,
    Tool,
    ToolCall,
    ToolRequestMessage,
    ToolResponseMessage,
)
from aviary.utils import ReaderWriterLock, format_exc, is_coroutine_callable

logger = logging.getLogger(__name__)

# TODO: make TypeVar after https://github.com/pydantic/pydantic/milestone/13
# NOTE: can't use pydantic.JsonValue here because it will deep copy all the way
# down JSON, and we want to support shallow copying capability
Serializable: TypeAlias = dict | list | int | float | str | bool | BaseModel


_T = TypeVar("_T")


async def maybe_wait_for(future: Awaitable[_T], timeout: float | None) -> _T:
    """Apply a timeout to an awaitable if one is provided, otherwise await indefinitely."""
    if timeout is None:
        return await future
    return await asyncio.wait_for(future, timeout)


class Frame(BaseModel):
    """A frame is a snapshot at a given timestep. The name comes from video frame."""

    deepcopy: bool = Field(
        default=True,
        description=(
            "Whether to deepcopy the state and info fields. "
            "Disable if you're sure they're immutable or desire mutability."
        ),
    )

    @staticmethod
    def _custom_serializer(value: Serializable | None, handler, info):  # noqa: ARG004
        if isinstance(value, BaseModel):
            return value.model_dump()
        return handler(value)

    state: Annotated[Serializable | None, WrapSerializer(_custom_serializer)] = Field(
        default=None,
        description=(
            "Either entire (or a subset of) the current state. Leave as default of None"
            " if state is irrelevant."
        ),
    )
    info: Annotated[Serializable | None, WrapSerializer(_custom_serializer)] = Field(
        default=None, description="Optional metadata that doesn't vary with state."
    )

    @field_validator("state", "info")
    @classmethod
    def make_deepcopy(
        cls, v: Serializable | None, info: ValidationInfo
    ) -> Serializable | None:
        if info.data["deepcopy"]:
            return deepcopy(v)
        return v


# NOTE: setting to None means there is no state
TEnvState = TypeVar("TEnvState")


class Environment(ABC, Generic[TEnvState]):
    """
    An environment is a stateful place where agents use tools and make observations.

    Tools are housed in the environment because they can interact with the environment.

    Environments (and their contained tools) are not trainable.
    """

    tools: list[Tool]
    state: TEnvState

    @abstractmethod
    async def step(
        self, action: ToolRequestMessage
    ) -> tuple[Messages, float, bool, bool]:
        """Take a step in the environment.

        Args:
            action: Action to take.

        Returns:
            Four-tuple of new observations, instantaneous reward for this action, a flag
                symbolizing if the episode is done, and a flag symbolizing if the
                episode was truncated (e.g. via early stopping).
        """

    @abstractmethod
    async def reset(self) -> tuple[Messages, list[Tool]]:
        """
        Reset the environment and collect initial observation(s).

        Possible observations could be instructions on how tools are related,
        or the goal of the environment.

        Returns:
            Two-tuple of initial observations and tools.
        """

    async def get_id(self) -> str:
        """
        Get an identifier for this environment.

        The main use case is something like the ID of the task from a dataset.
        Since datasets may not enforce uniqueness in their IDs, we cannot ensure the IDs
        returned from this method are unique either.

        The return should not be affected by state, in other words across reset/step,
        the return value should not change.

        This method is asynchronous to allow for DB transactions.
        """
        raise NotImplementedError(
            f"Getting ID is not yet implemented for environment {type(self).__name__}."
        )

    def filter_invalid_tool_calls(
        self, message: ToolRequestMessage
    ) -> tuple[ToolRequestMessage, ToolRequestMessage]:
        """Split a list of tool calls into valid and invalid subsets.

        Args:
            message: Tool request message containing tool calls.

        Returns:
            Two-tuple of ToolRequestMessage containing valid messages and
                ToolRequestMessage containing invalid messages
        """
        valid, invalid = [], []
        for tool_call in message.tool_calls:
            tool_used_in_tool_call = next(
                (t for t in self.tools if t.info.name == tool_call.function.name), None
            )
            if tool_used_in_tool_call is not None:
                valid.append(tool_call)
            else:
                invalid.append(tool_call)
        return cast(
            "tuple[ToolRequestMessage, ToolRequestMessage]",
            tuple(
                ToolRequestMessage(
                    role=message.role,
                    content=message.content,
                    function_call=message.function_call,
                    tool_calls=x,
                )
                for x in (valid, invalid)
            ),
        )

    TOOL_CALL_EXC_LOG_TB_NONDEBUG: ClassVar[bool] = os.environ.get(
        "AVIARY_TOOL_CALL_EXC_LOG_TB_NONDEBUG", "false"
    ).lower() in {"1", "true", "yes", "on"}

    async def exec_tool_calls(
        self,
        message: ToolRequestMessage,
        concurrency: bool = True,
        handle_tool_exc: bool = False,
        handle_invalid_tool_calls: bool = True,
        exec_timeout: float | None = None,
        **function_kwargs,
    ) -> list[ToolResponseMessage]:
        """
        Execute an ordered list of tool calls.

        Args:
            message: ToolRequestMessage containing the tool calls.
            concurrency: Flag to set True (default) to concurrently execute tool calls,
                otherwise set False to execute tool calls in the provided order.
            handle_tool_exc: Opt-in flag to suppress Exceptions and return them as a
                ToolResponseMessage.
            handle_invalid_tool_calls: Flag to handle invalid tool calls by returning
                a ToolResponseMessage with a note that the tool requested doesn't exist
            exec_timeout: Timeout for each tool call in seconds. If None, no timeout.
                Note that handle_tool_exec can be used to catch TimeoutErrors.
            **function_kwargs: Keyword arguments to pass to all tool functions.

        Returns:
            Ordered list of ToolResponseMessages, order matches the order of tool calls
                in the input message.
        """
        concurrency_lock = ReaderWriterLock()

        async def _exec_tool_call(tool_call: ToolCall) -> ToolResponseMessage:
            start = time.monotonic()
            try:
                tool = next(
                    t for t in self.tools if t.info.name == tool_call.function.name
                )
            except StopIteration as exc:
                raise ValueError(
                    f"{tool_call.function.name!r} not a valid name in"
                    f" { {t.info.name for t in self.tools} }."
                ) from exc

            # we do a special convenience to make
            # state be optional in the function signature
            need_to_filter = (
                "state" in function_kwargs
                and "state" not in inspect.signature(tool._tool_fn).parameters
                and not hasattr(tool._tool_fn, "requires_state")
            )
            filtered_kwargs = (
                {k: v for k, v in function_kwargs.items() if k != "state"}
                if need_to_filter
                else function_kwargs
            )

            concurrency_context = (
                concurrency_lock.read_lock()
                if tool.concurrency_safe
                else concurrency_lock.write_lock()
            )

            tool_exc: Exception | None = None
            try:
                async with concurrency_context:
                    if is_coroutine_callable(tool._tool_fn):
                        content = await maybe_wait_for(
                            tool._tool_fn(
                                **tool_call.function.arguments, **filtered_kwargs
                            ),
                            exec_timeout,
                        )
                    else:
                        # If the function is synchronous, run on a thread
                        content = await maybe_wait_for(
                            asyncio.to_thread(
                                tool._tool_fn,
                                **tool_call.function.arguments,
                                **filtered_kwargs,
                            ),
                            exec_timeout,
                        )
            except Exception as exc:
                if not handle_tool_exc:
                    raise
                logger_msg = (
                    f"Encountered exception during tool call"
                    f" for tool {tool.info.name}: {format_exc(exc)}"
                )
                if self.TOOL_CALL_EXC_LOG_TB_NONDEBUG:
                    logger.exception(logger_msg)
                else:
                    # logger.exception is just too verbose and clogs up console logging.
                    # This is a more human-friendly version:
                    # log a readable error message and emit the exception at DEBUG level.
                    logger.error(logger_msg)  # noqa: TRY400
                    logger.debug(str(exc), exc_info=True)
                tool_exc = exc
            if tool_exc:
                # No need to mention tool.info.name here, since it'll get wrapped in a ToolResponseMessage
                s_content = (
                    f"Encountered exception during tool call: {format_exc(tool_exc)}"
                )
            elif isinstance(content, str):
                s_content = content
            elif isinstance(content, BaseModel):
                s_content = content.model_dump_json(exclude_none=True, by_alias=True)
            else:  # Fallback when content is another type, or None
                s_content = json.dumps(content)
            return ToolResponseMessage.from_call(
                tool_call,
                content=s_content,
                info={
                    "start_ts": start,
                    "end_ts": time.monotonic(),
                },
            )

        invalid_responses = []
        valid_action = message
        call_ordering = [t.id for t in message.tool_calls]
        if handle_invalid_tool_calls:
            valid_action, invalid_action = self.filter_invalid_tool_calls(message)
            invalid_responses = [
                ToolResponseMessage.from_call(
                    tool_call, content=f"Invalid tool call: {tool_call.function.name}"
                )
                for tool_call in invalid_action.tool_calls
            ]

        if concurrency:
            valid_responses = await asyncio.gather(
                *(_exec_tool_call(tc) for tc in valid_action.tool_calls)
            )
        else:
            valid_responses = [
                await _exec_tool_call(tc) for tc in valid_action.tool_calls
            ]
        return sorted(
            invalid_responses + valid_responses,
            key=lambda x: call_ordering.index(x.tool_call_id),
        )

    def export_frame(self) -> Frame:
        """
        Export a snapshot of the environment as a Frame for visualization or debugging.

        If you are not sure what to put in the Frame, just give it the entire state.
        See the Frame class itself for more information.
        """
        return Frame()

    async def close(self) -> None:
        """
        Shutdown the environment.

        If this is unimplemented, __del__ will manage cleanup.
        """

    @classmethod
    def from_task(cls, task: str) -> Self:
        """Create an environment from a task description.

        A task is meant to be closer to a user prompt - like what you would expect
        in calling an LLM. This is how the environment should be used after training
        and in deployment. We don't take config here, because the default environment config
        should be general for arbitrary tasks.

        For example, with GSM8k/calculator: "What is 18 * (number of legs on a cat) / moons of mars?"
        """
        raise NotImplementedError(f"{cls.__name__} does not implement from_task")

    @classmethod
    def from_name(cls, name: str, task: str | None = None, **env_kwargs) -> Self:
        """Create an environment from the name of the class. Call `Environment.available()` to see list."""
        new_cls = _get_cls_from_name(ENV_REGISTRY, name)
        if task is not None:
            if env_kwargs:
                raise ValueError("Cannot pass both a task and environment kwargs.")
            return new_cls.from_task(task)
        return new_cls(**env_kwargs)

    @classmethod
    def available(cls) -> set[str]:
        """See list of available environment classes for `from_name`.

        This is not exhaustive, because some may be importable and so you should just
        try to call `from_name`. This is more for logging/debugging purposes.
        """
        return set(ENV_REGISTRY.keys())


# Maps baseline environment names to their module and class names
ENV_REGISTRY: dict[str, tuple[str, str]] = {
    "dummy": ("aviary.env", "DummyEnv"),
    "calculator": ("aviary.envs.gsm8k.env", "CalculatorEnv"),
    "hotpotqa": ("aviary.envs.hotpotqa.env", "HotPotQAEnv"),
}

TEnvironment = TypeVar("TEnvironment", bound=Environment)


class TaskDataset(ABC, Generic[TEnvironment]):
    """A base class for a dataset of tasks as environments.

    Examples of task datasets: GSM8k, HotPotQA, etc.
    These are related environments instances with different problem
    specifications and reward conditions.
    """

    @classmethod
    def from_name(cls, name: str, **env_kwargs) -> TaskDataset:
        return _get_cls_from_name(TASK_DATASET_REGISTRY, name)(**env_kwargs)

    def __len__(self) -> int:
        raise TypeError(f'"Object of type {self.__class__.__name__}" has no len()')

    def get_new_env_by_idx(self, idx: int) -> TEnvironment:
        """Get an env from a finite dataset."""
        raise NotImplementedError(
            f'"{self.__class__.__name__}" does not implement get_new_env_by_idx'
        )

    def get_new_env(self) -> TEnvironment:
        """Get an env from a non-indexable dataset."""
        raise NotImplementedError(
            f'"{self.__class__.__name__}" does not implement get_new_env'
        )

    def iter_batches(
        self, batch_size: int, shuffle: bool = False
    ) -> Iterator[list[TEnvironment]]:
        """Construct batches from this dataset.

        Args:
            batch_size: Size of each batch.
                Note that if this dataset's size is finite and isn't evenly divisible by
                this value, the last yielded batch will be smaller than batch_size.
            shuffle: Opt-in flag to shuffle without replacement.

        Yields:
            An iterator over batches of environments.
        """
        try:
            n = len(self)
        except TypeError:
            # not a finite-length dataset, so construct an infinite iter
            while True:
                yield [self.get_new_env() for _ in range(batch_size)]
        else:
            # finite-length dataset
            idcs = list(range(n))
            if shuffle:
                random.shuffle(idcs)

            while idcs:
                batch_idcs = idcs[:batch_size]
                idcs = idcs[batch_size:]
                yield [self.get_new_env_by_idx(idx) for idx in batch_idcs]


# Maps baseline task dataset names to their module and class names
TASK_DATASET_REGISTRY: dict[str, tuple[str, str]] = {
    "dummy": ("aviary.env", "DummyTaskDataset"),
    "gsm8k": ("aviary.envs.gsm8k.env", "GSM8kDataset"),
    "hotpotqa": ("aviary.envs.hotpotqa.env", "HotPotQADataset"),
}


class TaskConfig(BaseModel):
    """Convenience for making a config file entry for a TaskDataset."""

    model_config = ConfigDict(extra="forbid")

    name: str
    task_kwargs: dict[str, BaseModel | JsonValue] = Field(
        default_factory=dict, description="Arguments to pass to TaskDataset.from_name()"
    )
    train_kwargs: dict[str, BaseModel | JsonValue] = Field(
        default_factory=dict, description="Additional arguments for the training split."
    )
    eval_kwargs: dict[str, BaseModel | JsonValue] = Field(
        default_factory=dict,
        description="Additional arguments for the evaluation split.",
    )
    test_kwargs: dict[str, BaseModel | JsonValue] = Field(
        default_factory=dict, description="Additional arguments for the test split."
    )

    def make_dataset(self, split: str) -> TaskDataset:
        if split == "train":
            split_kw = self.task_kwargs | self.train_kwargs
        elif split == "eval":
            split_kw = self.task_kwargs | self.eval_kwargs
        elif split == "test":
            split_kw = self.task_kwargs | self.test_kwargs
        else:
            raise NotImplementedError(f"Didn't handle split {split!r}.")
        return TaskDataset.from_name(self.name, **split_kw)


class DummyEnvState(BaseModel):
    messages: Messages
    reward: float = 0
    done: bool = False


class DummyEnv(Environment[DummyEnvState]):
    """Simple Environment with basic functionality and no network usage."""

    State = DummyEnvState

    def __init__(
        self,
        task: str | None = None,
        end_immediately: bool = True,
        concurrent_tool_calls: bool = True,
    ):
        self.end_immediately = end_immediately
        self.task = task
        self.concurrent_tool_calls = concurrent_tool_calls

    async def get_id(self) -> str:
        if self.task is None:
            raise ValueError("No task (to reuse as an ID) was configured.")
        return self.task

    @classmethod
    def from_task(cls, task: str) -> DummyEnv:
        return cls(task=task)

    async def step(
        self, action: ToolRequestMessage
    ) -> tuple[Messages, float, bool, bool]:
        msgs: Messages = await self.exec_tool_calls(  # type: ignore[assignment]
            action, state=self.state, concurrency=self.concurrent_tool_calls
        ) or [Message(content=f"No tool calls input in tool request {action}.")]
        self.state.messages.extend(msgs)
        return msgs, self.state.reward, self.state.done, False

    async def reset(self) -> tuple[Messages, list[Tool]]:
        def print_story(story: str, state: DummyEnvState) -> None:  # noqa: ARG001
            """Print a story.

            Args:
                story: Story to print.
                state: Environment state.
            """
            state.reward = 1.0
            state.done = self.end_immediately

        def cast_float(x: str) -> float:
            """Cast the input argument x to a float."""
            return float(x)

        def cast_int(x: float) -> int:
            """Cast the input argument x to an integer."""
            return int(x)

        def get_random_int() -> int:
            """Get a random integer in 1 to 10."""
            return random.randint(1, 10)

        self.tools = [
            Tool.from_function(print_story),
            Tool.from_function(cast_float, allow_empty_param_descriptions=True),
            Tool.from_function(cast_int, allow_empty_param_descriptions=True),
            Tool.from_function(get_random_int, allow_empty_param_descriptions=True),
        ]
        self.state = type(self).State(
            messages=[
                Message(
                    content="Write a 5 word story via print_story"
                    + (f" about {self.task}" if self.task else "")
                )
            ],
        )
        return self.state.messages, self.tools

    def export_frame(self) -> Frame:
        return Frame(
            state={"messages": [m.content for m in self.state.messages]},
            info={
                "tool_names": [t.info.name for t in self.tools],
                "done": self.state.done,
                "reward": self.state.reward,
            },
        )


class DummyTaskDataset(TaskDataset[DummyEnv]):
    """A dummy task of infinite DummyEnvs."""

    def get_new_env(self) -> DummyEnv:
        return DummyEnv()

    def __bool__(self) -> bool:
        return True


def _get_cls_from_name(registry: dict[str, tuple[str, str]], name: str):
    try:
        module_name, cls_name = registry[name]
    except KeyError:
        raise ValueError(f"Unknown environment name: {name}") from None

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        # TODO: before release: add install instructions per env?
        raise ImportError(
            f"Could not import env from {module_name}; you need to install it."
        ) from None

    return getattr(module, cls_name)
