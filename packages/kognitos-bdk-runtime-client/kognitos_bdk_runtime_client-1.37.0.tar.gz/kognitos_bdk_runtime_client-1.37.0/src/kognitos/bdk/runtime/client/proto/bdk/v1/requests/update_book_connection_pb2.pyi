from bdk.v1.requests import authentication_pb2 as _authentication_pb2
from bdk.v1.requests import labels_pb2 as _labels_pb2
from bdk.v1.types import config_value_pb2 as _config_value_pb2
from bdk.v1.types import oauth_flow_pb2 as _oauth_flow_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class UpdateBookConnectionRequest(_message.Message):
    __slots__ = ('book_name', 'book_version', 'connection_id', 'authentication', 'config', 'labels', 'oauth_flow')
    BOOK_NAME_FIELD_NUMBER: _ClassVar[int]
    BOOK_VERSION_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICATION_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    OAUTH_FLOW_FIELD_NUMBER: _ClassVar[int]
    book_name: str
    book_version: str
    connection_id: str
    authentication: _authentication_pb2.Authentication
    config: _containers.RepeatedCompositeFieldContainer[_config_value_pb2.ConfigValue]
    labels: _containers.RepeatedCompositeFieldContainer[_labels_pb2.Label]
    oauth_flow: _oauth_flow_pb2.OAuthFlow

    def __init__(self, book_name: _Optional[str]=..., book_version: _Optional[str]=..., connection_id: _Optional[str]=..., authentication: _Optional[_Union[_authentication_pb2.Authentication, _Mapping]]=..., config: _Optional[_Iterable[_Union[_config_value_pb2.ConfigValue, _Mapping]]]=..., labels: _Optional[_Iterable[_Union[_labels_pb2.Label, _Mapping]]]=..., oauth_flow: _Optional[_Union[_oauth_flow_pb2.OAuthFlow, str]]=...) -> None:
        ...