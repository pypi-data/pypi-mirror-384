from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional
DESCRIPTOR: _descriptor.FileDescriptor

class BookConnectionOAuthCallbackRequest(_message.Message):
    __slots__ = ('code', 'state')
    CODE_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    code: str
    state: str

    def __init__(self, code: _Optional[str]=..., state: _Optional[str]=...) -> None:
        ...