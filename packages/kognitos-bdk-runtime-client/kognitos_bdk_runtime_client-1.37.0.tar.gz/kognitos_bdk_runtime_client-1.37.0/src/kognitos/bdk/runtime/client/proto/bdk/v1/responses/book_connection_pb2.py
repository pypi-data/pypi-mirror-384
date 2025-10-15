"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import book_connection_descriptor_pb2 as bdk_dot_v1_dot_types_dot_book__connection__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&bdk/v1/responses/book_connection.proto\x12\x06bdk.v1\x1a-bdk/v1/types/book_connection_descriptor.proto"\xea\x01\n\x16BookConnectionResponse\x12`\n\x1abook_connection_descriptor\x18\x01 \x01(\x0b2 .bdk.v1.BookConnectionDescriptorH\x00R\x18bookConnectionDescriptor\x12T\n\x0eoauth_redirect\x18\x02 \x01(\x0b2+.bdk.v1.BookConnectionOAuthRedirectResponseH\x00R\roauthRedirectB\x18\n\x16response_discriminator"7\n#BookConnectionOAuthRedirectResponse\x12\x10\n\x03url\x18\x01 \x01(\tR\x03urlB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.responses.book_connection_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKCONNECTIONRESPONSE']._serialized_start = 98
    _globals['_BOOKCONNECTIONRESPONSE']._serialized_end = 332
    _globals['_BOOKCONNECTIONOAUTHREDIRECTRESPONSE']._serialized_start = 334
    _globals['_BOOKCONNECTIONOAUTHREDIRECTRESPONSE']._serialized_end = 389