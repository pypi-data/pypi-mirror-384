from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Error(_message.Message):
    __slots__ = ("cause",)
    CAUSE_FIELD_NUMBER: _ClassVar[int]
    cause: str
    def __init__(self, cause: _Optional[str] = ...) -> None: ...

class Close(_message.Message):
    __slots__ = ("channel",)
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    channel: str
    def __init__(self, channel: _Optional[str] = ...) -> None: ...

class DataChunk(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...

class SendingMessage(_message.Message):
    __slots__ = ("localSequenceNumber", "channel", "data")
    LOCALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    localSequenceNumber: int
    channel: str
    data: bytes
    def __init__(self, localSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ..., data: _Optional[bytes] = ...) -> None: ...

class ReceivingMessage(_message.Message):
    __slots__ = ("globalSequenceNumber", "channel", "data")
    GLOBALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    globalSequenceNumber: int
    channel: str
    data: bytes
    def __init__(self, globalSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ..., data: _Optional[bytes] = ...) -> None: ...

class ReceivingStreamMessage(_message.Message):
    __slots__ = ("globalSequenceNumber", "channel")
    GLOBALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    globalSequenceNumber: int
    channel: str
    def __init__(self, globalSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ...) -> None: ...

class ReceivingStreamControl(_message.Message):
    __slots__ = ("streamSequenceNumber",)
    STREAMSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    streamSequenceNumber: int
    def __init__(self, streamSequenceNumber: _Optional[int] = ...) -> None: ...

class SendingStreamControl(_message.Message):
    __slots__ = ("globalSequenceNumber", "streamSequenceNumber")
    GLOBALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    STREAMSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    globalSequenceNumber: int
    streamSequenceNumber: int
    def __init__(self, globalSequenceNumber: _Optional[int] = ..., streamSequenceNumber: _Optional[int] = ...) -> None: ...

class StreamIdentify(_message.Message):
    __slots__ = ("localSequenceNumber", "channel", "runner")
    LOCALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    RUNNER_FIELD_NUMBER: _ClassVar[int]
    localSequenceNumber: int
    channel: str
    runner: str
    def __init__(self, localSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ..., runner: _Optional[str] = ...) -> None: ...

class StreamChunk(_message.Message):
    __slots__ = ("id", "data")
    ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    id: StreamIdentify
    data: DataChunk
    def __init__(self, id: _Optional[_Union[StreamIdentify, _Mapping]] = ..., data: _Optional[_Union[DataChunk, _Mapping]] = ...) -> None: ...

class GlobalAck(_message.Message):
    __slots__ = ("globalSequenceNumber", "channel")
    GLOBALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    globalSequenceNumber: int
    channel: str
    def __init__(self, globalSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ...) -> None: ...

class LocalAck(_message.Message):
    __slots__ = ("localSequenceNumber", "channel")
    LOCALSEQUENCENUMBER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    localSequenceNumber: int
    channel: str
    def __init__(self, localSequenceNumber: _Optional[int] = ..., channel: _Optional[str] = ...) -> None: ...
