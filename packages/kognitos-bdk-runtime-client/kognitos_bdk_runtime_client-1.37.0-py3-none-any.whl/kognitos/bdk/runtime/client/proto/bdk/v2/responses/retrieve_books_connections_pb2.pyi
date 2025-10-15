from bdk.v2.types import book_connection_descriptor_pb2 as _book_connection_descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RetrieveBooksConnectionsResponse(_message.Message):
    __slots__ = ('book_connections', 'next_page_token')
    BOOK_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    book_connections: _containers.RepeatedCompositeFieldContainer[_book_connection_descriptor_pb2.BookConnectionDescriptor]
    next_page_token: str

    def __init__(self, book_connections: _Optional[_Iterable[_Union[_book_connection_descriptor_pb2.BookConnectionDescriptor, _Mapping]]]=..., next_page_token: _Optional[str]=...) -> None:
        ...