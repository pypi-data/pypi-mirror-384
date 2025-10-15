from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class RetrieveBookConnectionsRequest(_message.Message):
    __slots__ = ('book_name', 'book_version', 'page_size', 'page_token')
    BOOK_NAME_FIELD_NUMBER: _ClassVar[int]
    BOOK_VERSION_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    book_name: str
    book_version: str
    page_size: int
    page_token: str

    def __init__(self, book_name: _Optional[str]=..., book_version: _Optional[str]=..., page_size: _Optional[int]=..., page_token: _Optional[str]=...) -> None:
        ...