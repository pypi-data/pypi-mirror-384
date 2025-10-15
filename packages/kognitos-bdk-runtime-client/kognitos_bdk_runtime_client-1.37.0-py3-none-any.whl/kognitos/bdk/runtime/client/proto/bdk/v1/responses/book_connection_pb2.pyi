from bdk.v1.types import book_connection_descriptor_pb2 as _book_connection_descriptor_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class BookConnectionResponse(_message.Message):
    __slots__ = ('book_connection_descriptor', 'oauth_redirect')
    BOOK_CONNECTION_DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    OAUTH_REDIRECT_FIELD_NUMBER: _ClassVar[int]
    book_connection_descriptor: _book_connection_descriptor_pb2.BookConnectionDescriptor
    oauth_redirect: BookConnectionOAuthRedirectResponse

    def __init__(self, book_connection_descriptor: _Optional[_Union[_book_connection_descriptor_pb2.BookConnectionDescriptor, _Mapping]]=..., oauth_redirect: _Optional[_Union[BookConnectionOAuthRedirectResponse, _Mapping]]=...) -> None:
        ...

class BookConnectionOAuthRedirectResponse(_message.Message):
    __slots__ = ('url',)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str

    def __init__(self, url: _Optional[str]=...) -> None:
        ...