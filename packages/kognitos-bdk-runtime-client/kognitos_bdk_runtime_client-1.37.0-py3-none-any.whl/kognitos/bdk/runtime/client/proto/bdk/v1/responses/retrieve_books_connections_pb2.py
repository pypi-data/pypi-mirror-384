"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import book_connection_descriptor_pb2 as bdk_dot_v1_dot_types_dot_book__connection__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n1bdk/v1/responses/retrieve_books_connections.proto\x12\x06bdk.v1\x1a-bdk/v1/types/book_connection_descriptor.proto"\xb0\x01\n RetrieveBooksConnectionsResponse\x12K\n\x10book_connections\x18\x01 \x03(\x0b2 .bdk.v1.BookConnectionDescriptorR\x0fbookConnections\x12+\n\x0fnext_page_token\x18\x02 \x01(\tH\x00R\rnextPageToken\x88\x01\x01B\x12\n\x10_next_page_tokenB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.responses.retrieve_books_connections_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RETRIEVEBOOKSCONNECTIONSRESPONSE']._serialized_start = 109
    _globals['_RETRIEVEBOOKSCONNECTIONSRESPONSE']._serialized_end = 285