from abc import ABC, abstractmethod
import re
from datetime import datetime
from typing import Dict, Any, List, Literal, Optional, Self, Union, override
import langchain_core.messages as langchain_messages
import langchain_core.messages.tool as langchain_messages_tool
from pydantic import BaseModel, Field, RootModel


class InvokeInput(BaseModel):
    """Basic user input for the agent."""

    message: str = Field(
        description="User input to the agent.",
        examples=["What is the weather in Tokyo?"],
    )
    # args: Dict[str, Any] = Field(
    #     description="Arguments to pass to the workflow.",
    #     default={},
    #     examples=[{"kb": "gts_support"}],
    # )
    # user: Optional[str] = Field(
    #     description="A user identifier to validate the user in knowledge bases and other tools.",
    #     default=None,
    #     examples=["jjohnson", "ccarlson"],
    # )
    # thread_id: str = Field(
    #     description="Thread ID to persist and continue a multi-turn conversation.",
    #     examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    # )


class StreamInput(InvokeInput):
    """User input for streaming the agent's response."""

    # stream_tokens: bool = Field(
    #     description="Whether to stream LLM tokens to the client.",
    #     default=True,
    # )
    # mode:


class AgentResponse(BaseModel):
    """Response from the agent when called via /invoke."""

    message: Dict[str, Any] = Field(
        description="Final response from the agent, as a serialized LangChain message.",
        examples=[
            {
                "message": {
                    "type": "ai",
                    "data": {
                        "content": "The weather in Tokyo is 70 degrees.",
                        "type": "ai",
                    },
                }
            }
        ],
    )


class BaseMessage[T: str, M: langchain_messages.BaseMessage](BaseModel, ABC):
    content: Union[str, list[Union[str, dict]]]
    """The string contents of the message."""

    type: T
    """
    The type of the message. Must be a string that is unique to the message type.

    The purpose of this field is to allow for easy identification of the message type
    when deserializing messages.
    """

    id: str = Field(coerce_numbers_to_str=True)
    """
    An optional unique identifier for the message. This should ideally be
    provided by the provider/model which created the message.
    """

    @classmethod
    @abstractmethod
    def from_lc_message(cls, message: M) -> Self:
        raise Exception("not implemented")


class BaseMessageChunk[
    MT: str,
    M: langchain_messages.BaseMessage,
    CT: str,
    C: langchain_messages.BaseMessageChunk,
](BaseMessage[MT, M], ABC):
    @classmethod
    @abstractmethod
    def from_lc_chunk(cls, chunk: C) -> Self:
        raise Exception("not implemented")


type MessageTypeHuman = Literal["human"]


class HumanMessage(BaseMessage[MessageTypeHuman, langchain_messages.HumanMessage]):
    """
    Message from a human.

    HumanMessages are messages that are passed in from a human to the model.
    """

    id: str = Field(default=..., coerce_numbers_to_str=True)

    type: MessageTypeHuman = "human"

    def to_langchain(self):
        return langchain_messages.HumanMessage(
            content=self.content,
        )

    @classmethod
    def from_lc_message(cls, message) -> Self:
        return cls(
            type="human",
            id=message.id,  # pyright: ignore[reportArgumentType]
            content=message.content,
        )


class ToolCall(BaseModel):
    """
    Represents a request to call a tool.
    """

    name: str
    """The name of the tool to be called."""
    args: dict[str, Any]
    """The arguments to the tool call."""
    id: Optional[str]
    """An identifier associated with the tool call.

    An identifier is needed to associate a tool call request with a tool
    call result in events when multiple concurrent tool calls are made.
    """
    type: Literal["tool_call"] = "tool_call"

    @classmethod
    def from_lc(cls, tool_call: langchain_messages_tool.ToolCall) -> Self:
        return cls(
            name=tool_call["name"],
            args=tool_call["args"],
            id=tool_call["id"],  # pyright: ignore[reportArgumentType]
        )


class ToolCallEvent(BaseModel):
    tool_call_id: str
    """Tool call that this message is responding to."""

    content: Union[str, list[Union[str, dict]], None] = Field(default=None)
    """The string contents of the message."""

    artifact: Any = None
    """
    Artifact of the Tool execution which is not meant to be sent to the model.
    """


class ToolCallChunk(BaseModel):
    """A chunk of a tool call (e.g., as part of a stream)."""

    name: Optional[str]
    """The name of the tool to be called."""
    args: Optional[str]
    """The arguments to the tool call."""
    id: Optional[str]
    """An identifier associated with the tool call."""
    index: Optional[int]
    """The index of the tool call in a sequence."""
    type: Literal["tool_call_chunk"] = "tool_call_chunk"

    @classmethod
    def from_lc(cls, tool_call_chunk: langchain_messages_tool.ToolCallChunk) -> Self:
        return cls(
            name=tool_call_chunk["name"],
            args=tool_call_chunk["args"],
            id=tool_call_chunk["id"],  # pyright: ignore[reportArgumentType]
            index=tool_call_chunk["index"],
        )


class InvalidToolCall(BaseModel):
    """Allowance for errors made by LLM.

    Here we add an `error` key to surface errors made during generation
    (e.g., invalid JSON arguments.)
    """

    name: Optional[str]
    """The name of the tool to be called."""
    args: Optional[str]
    """The arguments to the tool call."""
    id: Optional[str]
    """An identifier associated with the tool call."""
    error: Optional[str]
    """An error message associated with the tool call."""
    type: Literal["invalid_tool_call"] = "invalid_tool_call"

    @classmethod
    def from_lc(
        cls, invalid_tool_call: langchain_messages_tool.InvalidToolCall
    ) -> Self:
        return cls(
            name=invalid_tool_call["name"],
            args=invalid_tool_call["args"],
            id=invalid_tool_call["id"],  # pyright: ignore[reportArgumentType]
            error=invalid_tool_call["error"],
        )


type MessageTypeAI = Literal["ai"]


class AIMessage(BaseMessage[MessageTypeAI, langchain_messages.AIMessage]):
    """
    Message from an AI.

    AIMessage is returned from a chat model as a response to a prompt.

    This message represents the output of the model and consists of both
    the raw output as returned by the model together standardized fields
    (e.g., tool calls, usage metadata) added by the LangChain framework.
    """

    type: MessageTypeAI = "ai"

    tool_calls: list[ToolCall] = Field(default_factory=lambda: [])
    """If provided, tool calls associated with the message."""
    invalid_tool_calls: list[InvalidToolCall] = Field(default_factory=lambda: [])
    """If provided, tool calls with parsing errors associated with the message."""

    @classmethod
    def from_lc_message(cls, message) -> Self:
        return cls(
            id=message.id,  # pyright: ignore[reportArgumentType]
            content=message.content,
            tool_calls=[
                ToolCall.from_lc(tool_call) for tool_call in message.tool_calls
            ],
            invalid_tool_calls=[
                InvalidToolCall.from_lc(invalid_tool_call)
                for invalid_tool_call in message.invalid_tool_calls
            ],
        )


type MessageChunkTypeAI = Literal["ai_chunk"]


class AIMessageChunk(
    AIMessage,
    BaseMessageChunk[
        MessageTypeAI,
        langchain_messages.AIMessage,
        MessageChunkTypeAI,
        langchain_messages.AIMessageChunk,
    ],
):
    """Message chunk from an AI."""

    # Ignoring mypy re-assignment here since we're overriding the value
    # to make sure that the chunk variant can be discriminated from the
    # non-chunk variant.
    type: MessageChunkTypeAI = "ai_chunk"  # type: ignore[assignment]
    """The type of the message (used for deserialization).
    Defaults to "ai_chunk"."""

    tool_call_chunks: list[ToolCallChunk] = Field(default_factory=lambda: [])
    """If provided, tool call chunks associated with the message."""

    # TODO: other ai message fields?

    @classmethod
    def from_lc_chunk(cls, chunk) -> Self:
        c = cls.from_lc_message(chunk)
        c.type = "ai_chunk"
        c.tool_call_chunks = [
            ToolCallChunk.from_lc(tool_call_chunk)
            for tool_call_chunk in chunk.tool_call_chunks
        ]

        return c


type MessageTypeTool = Literal["tool"]


class ToolMessage(BaseMessage[MessageTypeTool, langchain_messages.ToolMessage]):
    """
    Message for passing the result of executing a tool back to a model.

    ToolMessages contain the result of a tool invocation. Typically, the result
    is encoded inside the `content` field.

    The tool_call_id field is used to associate the tool call request with the
    tool call response. This is useful in situations where a chat model is able
    to request multiple tool calls in parallel.
    """

    type: MessageTypeTool = "tool"

    tool_call_id: str
    """Tool call that this message is responding to."""

    artifact: Any = None
    """
    Artifact of the Tool execution which is not meant to be sent to the model.

    Should only be specified if it is different from the message content, e.g. if only
    a subset of the full tool output is being passed as message content but the full
    output is needed in other parts of the code.
    """

    status: Literal["pending", "success", "error"] = "success"
    """Status of the tool invocation."""

    @classmethod
    def from_lc_message(cls, message) -> Self:
        return cls(
            id=message.id,  # pyright: ignore[reportArgumentType]
            content=message.content,
            tool_call_id=message.tool_call_id,
            artifact=message.artifact,
            status=message.status,
        )


type MessageChunkTypeTool = Literal["tool_chunk"]


class ToolMessageChunk(
    ToolMessage,
    BaseMessageChunk[
        MessageTypeTool,
        langchain_messages.ToolMessage,
        MessageChunkTypeTool,
        langchain_messages.ToolMessageChunk,
    ],
):
    """Tool Message chunk."""

    # Ignoring mypy re-assignment here since we're overriding the value
    # to make sure that the chunk variant can be discriminated from the
    # non-chunk variant.
    type: MessageChunkTypeTool = "tool_chunk"  # type: ignore[assignment]
    """The type of the message (used for deserialization).
    Defaults to "tool_chunk"."""

    status: Literal["pending", "success", "error"] = "pending"

    @classmethod
    def from_lc_chunk(cls, chunk) -> Self:
        c = cls.from_lc_message(chunk)
        c.type = "tool_chunk"

        return c


AnyMessage = HumanMessage | AIMessage | ToolMessage


def api_message_from_langchain(message: langchain_messages.AnyMessage) -> AnyMessage:
    if isinstance(message, langchain_messages.HumanMessage):
        return HumanMessage.from_lc_message(message)
    elif isinstance(message, langchain_messages.AIMessage):
        return AIMessage.from_lc_message(message)
    elif isinstance(message, langchain_messages.ToolMessage):
        return ToolMessage.from_lc_message(message)
    else:
        raise Exception(
            f'unsupported langchain message type "{type(message)}": {message}'
        )


AnyMessageChunk = AIMessageChunk | ToolMessageChunk


def api_message_chunk_from_langchain(
    message: langchain_messages.AnyMessage,
) -> AnyMessageChunk:
    if isinstance(message, langchain_messages.AIMessageChunk):
        return AIMessageChunk.from_lc_chunk(message)
    elif isinstance(message, langchain_messages.ToolMessageChunk):
        return ToolMessageChunk.from_lc_chunk(message)
    elif isinstance(message, langchain_messages.ToolMessage):
        return ToolMessageChunk.from_lc_message(message)
    else:
        raise Exception(
            f'unsupported langchain message chunk type "{type(message)}": {message}'
        )


class AbstractStreamPayload(BaseModel):
    pass


class AbstractStreamData(AbstractStreamPayload):
    type: str
    content: Any

    @override
    def __str__(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


class StreamWarning(AbstractStreamData):
    type: Literal["warn"] = (  # pyright: ignore[reportIncompatibleVariableOverride]
        "warn"  
    )
    content: str


class StreamError(AbstractStreamData):
    type: Literal["error"] = ( # pyright: ignore[reportIncompatibleVariableOverride]
        "error"  
    )
    content: str


# class StreamToken(AbstractStreamData):
#     type: str = "token"
#     content: str


class StreamMessage(AbstractStreamData):
    type: Literal["message"] = ( # pyright: ignore[reportIncompatibleVariableOverride]
        "message"  
    )
    content: AnyMessage


class StreamMessageChunk(AbstractStreamData):
    type: Literal["message_chunk"] = ( # pyright: ignore[reportIncompatibleVariableOverride]
        "message_chunk"  
    )
    content: AnyMessageChunk


# class StreamToolEvent(AbstractStreamData):
#     type: Literal["tool_event"] = "tool_event"   # pyright: ignore[reportIncompatibleVariableOverride]
#     content: ToolCallEvent


class StreamDone(AbstractStreamPayload):
    @override
    def __str__(self) -> str:
        return "data: [DONE]\n\n"


AnyStreamEvent = (
    StreamWarning
    | StreamError
    | StreamMessage
    | StreamMessageChunk
    # | StreamToolEvent
    | StreamDone
)

# class Feedback(BaseModel):
#     """Feedback for a run."""

#     message_id: str = Field(
#         description="Message ID to record feedback for.",
#         examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
#     )
#     # thread_id: str = Field(
#     #     description="Thread ID to record feedback for.",
#     #     examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
#     # )
#     score: float = Field(
#         description="Feedback score.",
#         examples=[0.8],
#     )
#     kwargs: Dict[str, Any] = Field(
#         description="Additional feedback kwargs, passed to LangSmith.",
#         default={},
#         examples=[{"comment": "In-line human feedback"}],
#     )
#     creation: datetime = Field(default_factory=datetime.now)
