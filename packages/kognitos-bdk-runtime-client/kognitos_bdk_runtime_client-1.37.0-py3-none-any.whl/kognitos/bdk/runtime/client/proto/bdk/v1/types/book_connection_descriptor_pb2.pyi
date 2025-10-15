from bdk.v1.requests import authentication_pb2 as _authentication_pb2
from bdk.v1.requests import labels_pb2 as _labels_pb2
from bdk.v1.types import config_value_pb2 as _config_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class BookConnectionState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BOOK_CONNECTION_STATE_PENDING: _ClassVar[BookConnectionState]
    BOOK_CONNECTION_STATE_READY: _ClassVar[BookConnectionState]
    BOOK_CONNECTION_STATE_FAILED: _ClassVar[BookConnectionState]
BOOK_CONNECTION_STATE_PENDING: BookConnectionState
BOOK_CONNECTION_STATE_READY: BookConnectionState
BOOK_CONNECTION_STATE_FAILED: BookConnectionState

class BookConnectionDescriptor(_message.Message):
    __slots__ = ('book_name', 'book_version', 'connection_id', 'authentication', 'config', 'labels', 'state', 'endpoint')
    BOOK_NAME_FIELD_NUMBER: _ClassVar[int]
    BOOK_VERSION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    book_name: str
    book_version: str
    connection_id: str
    authentication: _authentication_pb2.Authentication
    config: _containers.RepeatedCompositeFieldContainer[_config_value_pb2.ConfigValue]
    labels: _containers.RepeatedCompositeFieldContainer[_labels_pb2.Label]
    state: BookConnectionState
    endpoint: str

    def __init__(self, book_name: _Optional[str]=..., book_version: _Optional[str]=..., connection_id: _Optional[str]=..., authentication: _Optional[_Union[_authentication_pb2.Authentication, _Mapping]]=..., config: _Optional[_Iterable[_Union[_config_value_pb2.ConfigValue, _Mapping]]]=..., labels: _Optional[_Iterable[_Union[_labels_pb2.Label, _Mapping]]]=..., state: _Optional[_Union[BookConnectionState, str]]=..., endpoint: _Optional[str]=...) -> None:
        ...