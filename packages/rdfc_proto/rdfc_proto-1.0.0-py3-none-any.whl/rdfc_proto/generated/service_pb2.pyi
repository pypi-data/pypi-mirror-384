from google.protobuf import empty_pb2 as _empty_pb2
import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LogMessage(_message.Message):
    __slots__ = ("level", "msg", "entities", "aliases")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    ENTITIES_FIELD_NUMBER: _ClassVar[int]
    ALIASES_FIELD_NUMBER: _ClassVar[int]
    level: str
    msg: str
    entities: _containers.RepeatedScalarFieldContainer[str]
    aliases: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, level: _Optional[str] = ..., msg: _Optional[str] = ..., entities: _Optional[_Iterable[str]] = ..., aliases: _Optional[_Iterable[str]] = ...) -> None: ...

class Processor(_message.Message):
    __slots__ = ("uri", "config", "arguments")
    URI_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    uri: str
    config: str
    arguments: str
    def __init__(self, uri: _Optional[str] = ..., config: _Optional[str] = ..., arguments: _Optional[str] = ...) -> None: ...

class ToRunner(_message.Message):
    __slots__ = ("proc", "start", "msg", "close", "streamMsg", "pipeline", "processed")
    PROC_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    CLOSE_FIELD_NUMBER: _ClassVar[int]
    STREAMMSG_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_FIELD_NUMBER: _ClassVar[int]
    proc: Processor
    start: _empty_pb2.Empty
    msg: _common_pb2.ReceivingMessage
    close: _common_pb2.Close
    streamMsg: _common_pb2.ReceivingStreamMessage
    pipeline: str
    processed: _common_pb2.LocalAck
    def __init__(self, proc: _Optional[_Union[Processor, _Mapping]] = ..., start: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ..., msg: _Optional[_Union[_common_pb2.ReceivingMessage, _Mapping]] = ..., close: _Optional[_Union[_common_pb2.Close, _Mapping]] = ..., streamMsg: _Optional[_Union[_common_pb2.ReceivingStreamMessage, _Mapping]] = ..., pipeline: _Optional[str] = ..., processed: _Optional[_Union[_common_pb2.LocalAck, _Mapping]] = ...) -> None: ...

class ProcessorInitialized(_message.Message):
    __slots__ = ("uri", "error")
    URI_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    uri: str
    error: _common_pb2.Error
    def __init__(self, uri: _Optional[str] = ..., error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ...) -> None: ...

class RunnerIdentify(_message.Message):
    __slots__ = ("uri",)
    URI_FIELD_NUMBER: _ClassVar[int]
    uri: str
    def __init__(self, uri: _Optional[str] = ...) -> None: ...

class FromRunner(_message.Message):
    __slots__ = ("initialized", "close", "identify", "msg", "processed")
    INITIALIZED_FIELD_NUMBER: _ClassVar[int]
    CLOSE_FIELD_NUMBER: _ClassVar[int]
    IDENTIFY_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_FIELD_NUMBER: _ClassVar[int]
    initialized: ProcessorInitialized
    close: _common_pb2.Close
    identify: RunnerIdentify
    msg: _common_pb2.SendingMessage
    processed: _common_pb2.GlobalAck
    def __init__(self, initialized: _Optional[_Union[ProcessorInitialized, _Mapping]] = ..., close: _Optional[_Union[_common_pb2.Close, _Mapping]] = ..., identify: _Optional[_Union[RunnerIdentify, _Mapping]] = ..., msg: _Optional[_Union[_common_pb2.SendingMessage, _Mapping]] = ..., processed: _Optional[_Union[_common_pb2.GlobalAck, _Mapping]] = ...) -> None: ...
