import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateConversationRequest(_message.Message):
    __slots__ = ("workspace_rid", "workbook_rid", "message", "title")
    WORKSPACE_RID_FIELD_NUMBER: _ClassVar[int]
    WORKBOOK_RID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    workspace_rid: str
    workbook_rid: str
    message: ModelMessage
    title: str
    def __init__(self, workspace_rid: _Optional[str] = ..., workbook_rid: _Optional[str] = ..., message: _Optional[_Union[ModelMessage, _Mapping]] = ..., title: _Optional[str] = ...) -> None: ...

class CreateConversationResponse(_message.Message):
    __slots__ = ("conversation_rid",)
    CONVERSATION_RID_FIELD_NUMBER: _ClassVar[int]
    conversation_rid: str
    def __init__(self, conversation_rid: _Optional[str] = ...) -> None: ...

class ListConversationsRequest(_message.Message):
    __slots__ = ("workbook_rid", "limit", "cursor")
    WORKBOOK_RID_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    workbook_rid: str
    limit: int
    cursor: str
    def __init__(self, workbook_rid: _Optional[str] = ..., limit: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class ListConversationsResponse(_message.Message):
    __slots__ = ("conversations", "next_cursor")
    CONVERSATIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    conversations: _containers.RepeatedCompositeFieldContainer[ConversationMetadata]
    next_cursor: str
    def __init__(self, conversations: _Optional[_Iterable[_Union[ConversationMetadata, _Mapping]]] = ..., next_cursor: _Optional[str] = ...) -> None: ...

class GetConversationRequest(_message.Message):
    __slots__ = ("conversation_rid",)
    CONVERSATION_RID_FIELD_NUMBER: _ClassVar[int]
    conversation_rid: str
    def __init__(self, conversation_rid: _Optional[str] = ...) -> None: ...

class GetConversationResponse(_message.Message):
    __slots__ = ("conversation",)
    CONVERSATION_FIELD_NUMBER: _ClassVar[int]
    conversation: Conversation
    def __init__(self, conversation: _Optional[_Union[Conversation, _Mapping]] = ...) -> None: ...

class AddMessageRequest(_message.Message):
    __slots__ = ("conversation_rid", "message")
    CONVERSATION_RID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    conversation_rid: str
    message: ModelMessage
    def __init__(self, conversation_rid: _Optional[str] = ..., message: _Optional[_Union[ModelMessage, _Mapping]] = ...) -> None: ...

class AddMessageResponse(_message.Message):
    __slots__ = ("message_id",)
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    def __init__(self, message_id: _Optional[str] = ...) -> None: ...

class SetConversationTitleRequest(_message.Message):
    __slots__ = ("conversation_rid", "title")
    CONVERSATION_RID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    conversation_rid: str
    title: str
    def __init__(self, conversation_rid: _Optional[str] = ..., title: _Optional[str] = ...) -> None: ...

class SetConversationTitleResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConversationMetadata(_message.Message):
    __slots__ = ("rid", "workbook_rid", "title", "created_at", "updated_at")
    RID_FIELD_NUMBER: _ClassVar[int]
    WORKBOOK_RID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    rid: str
    workbook_rid: str
    title: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, rid: _Optional[str] = ..., workbook_rid: _Optional[str] = ..., title: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ModelMessage(_message.Message):
    __slots__ = ("id", "created_at", "user", "assistant")
    ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ASSISTANT_FIELD_NUMBER: _ClassVar[int]
    id: str
    created_at: _timestamp_pb2.Timestamp
    user: UserModelMessage
    assistant: AssistantModelMessage
    def __init__(self, id: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., user: _Optional[_Union[UserModelMessage, _Mapping]] = ..., assistant: _Optional[_Union[AssistantModelMessage, _Mapping]] = ...) -> None: ...

class Conversation(_message.Message):
    __slots__ = ("metadata", "messages")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    metadata: ConversationMetadata
    messages: _containers.RepeatedCompositeFieldContainer[ModelMessage]
    def __init__(self, metadata: _Optional[_Union[ConversationMetadata, _Mapping]] = ..., messages: _Optional[_Iterable[_Union[ModelMessage, _Mapping]]] = ...) -> None: ...

class UserModelMessage(_message.Message):
    __slots__ = ("parts",)
    PARTS_FIELD_NUMBER: _ClassVar[int]
    parts: _containers.RepeatedCompositeFieldContainer[UserContentPart]
    def __init__(self, parts: _Optional[_Iterable[_Union[UserContentPart, _Mapping]]] = ...) -> None: ...

class AssistantModelMessage(_message.Message):
    __slots__ = ("parts",)
    PARTS_FIELD_NUMBER: _ClassVar[int]
    parts: _containers.RepeatedCompositeFieldContainer[AssistantContentPart]
    def __init__(self, parts: _Optional[_Iterable[_Union[AssistantContentPart, _Mapping]]] = ...) -> None: ...

class UserContentPart(_message.Message):
    __slots__ = ("text", "image")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    text: TextPart
    image: ImagePart
    def __init__(self, text: _Optional[_Union[TextPart, _Mapping]] = ..., image: _Optional[_Union[ImagePart, _Mapping]] = ...) -> None: ...

class AssistantContentPart(_message.Message):
    __slots__ = ("text", "reasoning", "tool_action")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    TOOL_ACTION_FIELD_NUMBER: _ClassVar[int]
    text: TextPart
    reasoning: ReasoningPart
    tool_action: ToolActionPart
    def __init__(self, text: _Optional[_Union[TextPart, _Mapping]] = ..., reasoning: _Optional[_Union[ReasoningPart, _Mapping]] = ..., tool_action: _Optional[_Union[ToolActionPart, _Mapping]] = ...) -> None: ...

class TextPart(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class ImagePart(_message.Message):
    __slots__ = ("s3_uri", "media_type")
    S3_URI_FIELD_NUMBER: _ClassVar[int]
    MEDIA_TYPE_FIELD_NUMBER: _ClassVar[int]
    s3_uri: str
    media_type: str
    def __init__(self, s3_uri: _Optional[str] = ..., media_type: _Optional[str] = ...) -> None: ...

class ReasoningPart(_message.Message):
    __slots__ = ("reasoning",)
    REASONING_FIELD_NUMBER: _ClassVar[int]
    reasoning: str
    def __init__(self, reasoning: _Optional[str] = ...) -> None: ...

class ToolActionPart(_message.Message):
    __slots__ = ("id", "tool_action_verb", "tool_target")
    ID_FIELD_NUMBER: _ClassVar[int]
    TOOL_ACTION_VERB_FIELD_NUMBER: _ClassVar[int]
    TOOL_TARGET_FIELD_NUMBER: _ClassVar[int]
    id: str
    tool_action_verb: str
    tool_target: str
    def __init__(self, id: _Optional[str] = ..., tool_action_verb: _Optional[str] = ..., tool_target: _Optional[str] = ...) -> None: ...
