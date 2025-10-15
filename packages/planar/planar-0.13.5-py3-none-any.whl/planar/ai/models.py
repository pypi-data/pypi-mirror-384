from enum import Enum
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, Field
from pydantic_ai.settings import ModelSettings

from planar.files.models import PlanarFile
from planar.modeling.field_helpers import JsonSchema
from planar.object_config.object_config import (
    ObjectConfigurationBase,
)

# Type variable for output_type, which can be str or a Pydantic model
T = TypeVar("T", bound=Union[str, BaseModel])


# Agent configuration overrides.
# This model allows storing configurations that override the default
# settings defined in Agent instances.
class AgentConfig(BaseModel):
    # ModelSettings TypedDict has some fields that use non-serializable types
    # so we need to allow arbitrary types
    model_config = {"arbitrary_types_allowed": True}
    system_prompt: str
    user_prompt: str = Field()
    model: str = Field()
    max_turns: int = Field()
    # `ModelSettings` is a TypedDict; use a typed empty dict as default
    model_parameters: ModelSettings = Field(
        default_factory=lambda: cast(ModelSettings, {})
    )


class ToolDefinition(BaseModel):
    """Defines a tool that the model can call."""

    name: str
    description: str
    # This is a json schema string
    parameters: Dict[str, Any]


class ToolCall(BaseModel):
    """Represents a tool call made by the model."""

    id: Optional[str] = None  # Optional ID, included by providers like OpenAI
    name: str
    arguments: Dict[str, Any]  # Arguments for the tool call, as a dictionary


class ToolResponse(BaseModel):
    """Represents a response to a tool call."""

    tool_call_id: Optional[str] = None  # ID of the corresponding tool call
    content: str  # String content of the tool response


class ModelMessage(BaseModel):
    """Base class for messages exchanged with LLM providers."""

    content: Optional[str] = None


class AssistantMessage(ModelMessage):
    """Message from the assistant, may include tool calls."""

    tool_calls: Optional[List[ToolCall]] = None


class UserMessage(ModelMessage):
    """Message from the user."""

    files: Optional[list[PlanarFile]] = None


class SystemMessage(ModelMessage):
    """System message that provides context/instructions."""

    pass


class ToolMessage(ModelMessage):
    """Tool message containing a tool response."""

    tool_call_id: str  # ID of the tool call this is responding to


# Define JsonData type as a union of valid JSON values
JsonData = str | int | float | bool | None | dict[str, Any] | list[Any]


class ToolCallResult(BaseModel):
    tool_call_id: str
    tool_call_name: str
    content: BaseModel | JsonData


class CompletionResponse[T: BaseModel | str](BaseModel):
    """Response object that may contain content or tool calls."""

    content: Optional[T] = None  # Content as str or parsed Pydantic model
    text_content: Optional[str] = (
        None  # Optional text content, if separate from structured output
    )
    reasoning_content: Optional[str] = None  # Optional reasoning content
    tool_calls: Optional[List[ToolCall]] = None  # List of tool calls, if any


class AgentRunResult[TOutput: BaseModel | str](BaseModel):
    output: TOutput


class Base64Content(BaseModel):
    type: Literal["base64"] = "base64"
    content: str
    content_type: str

    def __repr__(self):
        return f"Base64Content(content_type={self.content_type}, content={self.content[:10]}...)"


class URLContent(BaseModel):
    type: Literal["url"] = "url"
    content: str


class FileIdContent(BaseModel):
    type: Literal["file_id"] = "file_id"
    content: str


FileContent = Annotated[
    Union[Base64Content, URLContent, FileIdContent],
    Field(discriminator="type"),
]


class FileMap(BaseModel):
    mapping: dict[str, FileContent]


class AgentSerializeable(BaseModel):
    name: str
    input_schema: JsonSchema | None = None
    output_schema: JsonSchema | None = None
    tool_definitions: list[dict[str, Any]]
    configs: list[ObjectConfigurationBase[AgentConfig]]

    # TODO: actually fetch built_in_vars from agent object
    built_in_vars: dict[str, str] = Field(default_factory=dict)


class AgentEventType(str, Enum):
    """Valid event types that can be emitted by an Agent."""

    RESPONSE = "response"
    TOOL_RESPONSE = "tool_response"
    COMPLETED = "completed"
    ERROR = "error"
    THINK = "think"
    TEXT = "text"


class AgentEventEmitter(Protocol):
    def emit(self, event_type: AgentEventType, data: BaseModel | str | None): ...
