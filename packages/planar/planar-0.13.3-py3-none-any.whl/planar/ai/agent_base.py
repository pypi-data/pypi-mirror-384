import abc
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Coroutine,
    Type,
    cast,
    overload,
)

from pydantic import BaseModel
from pydantic_ai.settings import ModelSettings

from planar.ai.models import AgentConfig, AgentEventEmitter, AgentRunResult
from planar.ai.tool_context import clear_tool_context, set_tool_context
from planar.logging import get_logger
from planar.modeling.field_helpers import JsonSchema
from planar.utils import P, R, T, U
from planar.workflows import as_step
from planar.workflows.models import StepType

logger = get_logger(__name__)


@dataclass
class AgentBase[
    # TODO: add `= str` default when we upgrade to 3.13
    TInput: BaseModel | str,
    TOutput: BaseModel | str,
    TToolContext,
](abc.ABC):
    """An LLM-powered agent that can be called directly within workflows."""

    name: str
    system_prompt: str
    output_type: Type[TOutput] | None = None
    input_type: Type[TInput] | None = None
    user_prompt: str = ""
    tools: list[Callable] = field(default_factory=list)
    max_turns: int = 2
    # `ModelSettings` is a TypedDict; use a typed empty dict as default
    model_parameters: ModelSettings = field(
        default_factory=lambda: cast(ModelSettings, {})
    )
    event_emitter: AgentEventEmitter | None = None
    durable: bool = True
    tool_context_type: Type[TToolContext] | None = None

    # TODO: move here to serialize to frontend
    #
    # built_in_vars: Dict[str, str] = field(default_factory=lambda: {
    #     "datetime_now": datetime.datetime.now().isoformat(),
    #     "date_today": datetime.date.today().isoformat(),
    # })

    def __post_init__(self):
        if self.input_type:
            if (
                not issubclass(self.input_type, BaseModel)
                and self.input_type is not str
            ):
                raise ValueError(
                    "input_type must be 'str' or a subclass of a Pydantic model"
                )
        if self.max_turns < 1:
            raise ValueError("Max_turns must be greater than or equal to 1.")
        if self.tools and self.max_turns <= 1:
            raise ValueError(
                "For tool calling to work, max_turns must be greater than 1."
            )

    def input_schema(self) -> JsonSchema | None:
        if self.input_type is None:
            return None
        if self.input_type is str:
            return None
        assert issubclass(self.input_type, BaseModel), (
            "input_type must be a subclass of BaseModel or str"
        )
        return self.input_type.model_json_schema()

    def output_schema(self) -> JsonSchema | None:
        if self.output_type is None:
            return None
        if self.output_type is str:
            return None
        assert issubclass(self.output_type, BaseModel), (
            "output_type must be a subclass of BaseModel or str"
        )
        return self.output_type.model_json_schema()

    @overload
    async def __call__(
        self: "AgentBase[TInput, str, TToolContext]",
        input_value: TInput,
        tool_context: TToolContext | None = None,
    ) -> AgentRunResult[str]: ...

    @overload
    async def __call__(
        self: "AgentBase[TInput, TOutput, TToolContext]",
        input_value: TInput,
        tool_context: TToolContext | None = None,
    ) -> AgentRunResult[TOutput]: ...

    def as_step_if_durable(
        self,
        func: Callable[P, Coroutine[T, U, R]],
        step_type: StepType,
        display_name: str | None = None,
        return_type: Type[R] | None = None,
    ) -> Callable[P, Coroutine[T, U, R]]:
        if not self.durable:
            return func
        return as_step(
            func,
            step_type=step_type,
            display_name=display_name or self.name,
            return_type=return_type,
        )

    async def __call__(
        self,
        input_value: TInput,
        tool_context: TToolContext | None = None,
    ) -> AgentRunResult[Any]:
        if self.input_type is not None and not isinstance(input_value, self.input_type):
            raise ValueError(
                f"Input value must be of type {self.input_type}, but got {type(input_value)}"
            )
        elif not isinstance(input_value, (str, BaseModel)):
            # Should not happen based on type constraints, but just in case
            # user does not have type checking enabled
            raise ValueError(
                "Input value must be a string or a Pydantic model if input_type is not provided"
            )

        if self.output_type is None:
            run_step = self.as_step_if_durable(
                self.run_step,
                step_type=StepType.AGENT,
                display_name=self.name,
                return_type=AgentRunResult[str],
            )
        else:
            run_step = self.as_step_if_durable(
                self.run_step,
                step_type=StepType.AGENT,
                display_name=self.name,
                return_type=AgentRunResult[self.output_type],
            )

        if tool_context is not None:
            if self.tool_context_type is None:
                raise ValueError(
                    "tool_context cannot be provided when tool_context_type is not set"
                )
            if not isinstance(tool_context, self.tool_context_type):
                raise ValueError(
                    f"tool_context must be of type {self.tool_context_type}, "
                    f"but got {type(tool_context)}"
                )
            set_tool_context(cast(TToolContext, tool_context))

        try:
            result = await run_step(input_value=input_value)
            # Cast the result to ensure type compatibility
            return cast(AgentRunResult[TOutput], result)
        finally:
            if tool_context is not None:
                clear_tool_context()

    @abc.abstractmethod
    async def run_step(
        self,
        input_value: TInput,
    ) -> AgentRunResult[TOutput]: ...

    @abc.abstractmethod
    def get_model_str(self) -> str: ...

    def to_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt,
            model=self.get_model_str(),
            max_turns=self.max_turns,
            model_parameters=self.model_parameters,
        )
