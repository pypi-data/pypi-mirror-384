"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import book_descriptor_pb2 as bdk_dot_v1_dot_types_dot_book__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$bdk/v1/responses/retrieve_book.proto\x12\x06bdk.v1\x1a"bdk/v1/types/book_descriptor.proto"B\n\x14RetrieveBookResponse\x12*\n\x04book\x18\x01 \x01(\x0b2\x16.bdk.v1.BookDescriptorR\x04bookB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.responses.retrieve_book_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RETRIEVEBOOKRESPONSE']._serialized_start = 84
    _globals['_RETRIEVEBOOKRESPONSE']._serialized_end = 150