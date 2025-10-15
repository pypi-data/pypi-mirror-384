from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class RemoveBookConnectionRequest(_message.Message):
    __slots__ = ('connection_id', 'book_name', 'book_version')
    CONNECTION_ID_FIELD_NUMBER: _ClassVar[int]
    BOOK_NAME_FIELD_NUMBER: _ClassVar[int]
    BOOK_VERSION_FIELD_NUMBER: _ClassVar[int]
    connection_id: str
    book_name: str
    book_version: str

    def __init__(self, connection_id: _Optional[str]=..., book_name: _Optional[str]=..., book_version: _Optional[str]=...) -> None:
        ...