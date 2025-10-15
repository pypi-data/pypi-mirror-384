"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import value_pb2 as bdk_dot_v1_dot_types_dot_value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$bdk/v1/requests/authentication.proto\x12\x06bdk.v1\x1a\x18bdk/v1/types/value.proto"\x95\x01\n\x0eAuthentication\x12+\n\x11authentication_id\x18\x03 \x01(\tR\x10authenticationId\x12V\n\x1aauthentication_credentials\x18\x04 \x03(\x0b2\x17.bdk.v1.CredentialValueR\x19authenticationCredentials"F\n\x0fCredentialValue\x12\x0e\n\x02id\x18\x01 \x01(\tR\x02id\x12#\n\x05value\x18\x02 \x01(\x0b2\r.bdk.v1.ValueR\x05valueB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.requests.authentication_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_AUTHENTICATION']._serialized_start = 75
    _globals['_AUTHENTICATION']._serialized_end = 224
    _globals['_CREDENTIALVALUE']._serialized_start = 226
    _globals['_CREDENTIALVALUE']._serialized_end = 296