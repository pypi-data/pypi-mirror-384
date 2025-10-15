from bdk.v1.types import user_info_pb2 as _user_info_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RetrieveUserInfoResponse(_message.Message):
    __slots__ = ('user_info',)
    USER_INFO_FIELD_NUMBER: _ClassVar[int]
    user_info: _user_info_pb2.UserInfo

    def __init__(self, user_info: _Optional[_Union[_user_info_pb2.UserInfo, _Mapping]]=...) -> None:
        ...