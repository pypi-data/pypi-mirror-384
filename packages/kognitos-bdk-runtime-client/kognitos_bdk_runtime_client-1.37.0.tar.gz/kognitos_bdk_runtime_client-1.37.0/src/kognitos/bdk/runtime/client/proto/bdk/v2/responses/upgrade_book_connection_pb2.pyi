from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class UpgradeBookConnectionResponse(_message.Message):
    __slots__ = ('connection_id',)
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    connection_id: str

    def __init__(self, connection_id: _Optional[str]=...) -> None:
        ...