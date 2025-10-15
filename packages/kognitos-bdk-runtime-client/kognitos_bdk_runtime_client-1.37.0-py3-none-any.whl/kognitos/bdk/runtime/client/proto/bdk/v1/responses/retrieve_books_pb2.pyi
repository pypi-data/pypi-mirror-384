from bdk.v1.types import book_descriptor_pb2 as _book_descriptor_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RetrieveBooksResponse(_message.Message):
    __slots__ = ('books', 'next_page_token')
    BOOKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_PAGE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    books: _containers.RepeatedCompositeFieldContainer[_book_descriptor_pb2.BookDescriptor]
    next_page_token: str

    def __init__(self, books: _Optional[_Iterable[_Union[_book_descriptor_pb2.BookDescriptor, _Mapping]]]=..., next_page_token: _Optional[str]=...) -> None:
        ...