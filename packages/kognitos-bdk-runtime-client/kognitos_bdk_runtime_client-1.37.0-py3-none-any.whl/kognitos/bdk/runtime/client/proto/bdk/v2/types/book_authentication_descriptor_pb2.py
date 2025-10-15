"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import book_custom_authentication_descriptor_pb2 as bdk_dot_v2_dot_types_dot_book__custom__authentication__descriptor__pb2
from ....bdk.v2.types import book_oauh_authentication_descriptor_pb2 as bdk_dot_v2_dot_types_dot_book__oauh__authentication__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n1bdk/v2/types/book_authentication_descriptor.proto\x12\x06bdk.v2\x1a8bdk/v2/types/book_custom_authentication_descriptor.proto\x1a6bdk/v2/types/book_oauh_authentication_descriptor.proto"\xc7\x01\n\x1cBookAuthenticationDescriptor\x12D\n\x06custom\x18\x01 \x01(\x0b2*.bdk.v2.BookCustomAuthenticationDescriptorH\x00R\x06custom\x12A\n\x05oauth\x18\x02 \x01(\x0b2).bdk.v2.BookOAuthAuthenticationDescriptorH\x00R\x05oauthB\x1e\n\x1cauthentication_discriminatorB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.book_authentication_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKAUTHENTICATIONDESCRIPTOR']._serialized_start = 176
    _globals['_BOOKAUTHENTICATIONDESCRIPTOR']._serialized_end = 375