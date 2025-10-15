import contextlib
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pydantic import BaseModel, Field, ValidationError

from aviary.message import MalformedMessageError, Message

from .base import (
    MessagesAdapter,
    Tool,
    ToolRequestMessage,
    ToolResponseMessage,
    ToolsAdapter,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from litellm import ModelResponse


class ToolSelector:
    """Simple entity to select a tool based on messages."""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        acompletion: "Callable[..., Awaitable[ModelResponse]] | None" = None,
        accum_messages: bool = False,
    ):
        """Initialize.

        Args:
            model_name: Name of the model to select a tool with.
            acompletion: Optional async completion function to use, leaving as the
                default of None will use LiteLLM's acompletion. Alternately, specify
                LiteLLM's Router.acompletion function for centralized rate limiting.
            accum_messages: Whether the selector should accumulate messages in a ledger.
        """
        self._add_stop_reason_on_tool_choice_of_tool = True
        if acompletion is None:
            try:
                from litellm import acompletion
                from litellm._version import version as litellm_version  # noqa: PLC2701
                from packaging import version
            except ImportError as e:
                raise ImportError(
                    f"{type(self).__name__} requires the 'llm' extra for"
                    " 'litellm' and 'packaging'. Please: `pip install aviary[llm]`."
                ) from e
            with contextlib.suppress(version.InvalidVersion):
                # litellm>=1.72.0 fixed the `finish_reason` being "stop"
                # (instead of "tool_calls") when specifying a `tool_choice` as a `Tool`
                self._add_stop_reason_on_tool_choice_of_tool = version.parse(
                    litellm_version
                ) < version.parse("1.72.0")

        self._model_name = model_name
        self._bound_acompletion = partial(cast("Callable", acompletion), model_name)
        self._ledger = ToolSelectorLedger() if accum_messages else None

    # SEE: https://platform.openai.com/docs/api-reference/chat/create#chat-create-tool_choice
    # > `required` means the model must call one or more tools.
    TOOL_CHOICE_REQUIRED: ClassVar[str] = "required"

    async def __call__(
        self,
        messages: list[Message],
        tools: list[Tool],
        tool_choice: Tool | str | None = TOOL_CHOICE_REQUIRED,
    ) -> ToolRequestMessage:
        """Run a completion that selects a tool in tools given the messages."""
        completion_kwargs: dict[str, Any] = {}
        # SEE: https://platform.openai.com/docs/guides/function-calling/configuring-function-calling-behavior-using-the-tool_choice-parameter
        expected_finish_reason: set[str] = {"tool_calls"}
        if isinstance(tool_choice, Tool):
            completion_kwargs["tool_choice"] = {
                "type": "function",
                "function": {"name": tool_choice.info.name},
            }
            if self._add_stop_reason_on_tool_choice_of_tool:
                expected_finish_reason.add("stop")
        elif tool_choice is not None:
            completion_kwargs["tool_choice"] = tool_choice
            if tool_choice == self.TOOL_CHOICE_REQUIRED:
                # Even though docs say it should be just 'stop',
                # in practice 'tool_calls' shows up too
                expected_finish_reason.add("stop")

        if self._ledger is not None:
            self._ledger.messages.extend(messages)
            messages = self._ledger.messages

        model_response = await self._bound_acompletion(
            messages=MessagesAdapter.dump_python(
                messages, exclude_none=True, by_alias=True
            ),
            tools=ToolsAdapter.dump_python(tools, exclude_none=True, by_alias=True),
            **completion_kwargs,
        )

        if (num_choices := len(model_response.choices)) != 1:
            raise MalformedMessageError(
                f"Expected one choice in model response, got {num_choices}"
                f" choices, full response was {model_response}."
            )
        choice = model_response.choices[0]
        if choice.finish_reason not in expected_finish_reason:
            raise MalformedMessageError(
                f"Expected a finish reason in {expected_finish_reason} in"
                f" model response, got finish reason {choice.finish_reason!r}, full"
                f" response was {model_response} and tool choice was {tool_choice!r}."
            )
        usage = model_response.usage
        try:
            selection = ToolRequestMessage(
                **choice.message.model_dump(),
                info={
                    "usage": (usage.prompt_tokens, usage.completion_tokens),
                    "model": self._model_name,
                },
            )
        except ValidationError as exc:
            raise MalformedMessageError(
                f"Failed to convert model response's message {choice.message}"
                f" into a tool request message."
                f" Got finish reason {choice.finish_reason!r}, full"
                f" response was {model_response} and tool choice was {tool_choice!r}."
            ) from exc
        if self._ledger is not None:
            self._ledger.messages.append(selection)
        return selection


class ToolSelectorLedger(BaseModel):
    """Simple ledger to record tools and messages."""

    tools: list[Tool] = Field(default_factory=list)
    messages: list[ToolRequestMessage | ToolResponseMessage | Message] = Field(
        default_factory=list
    )
