"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.requests import authentication_pb2 as bdk_dot_v1_dot_requests_dot_authentication__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%bdk/v1/requests/test_connection.proto\x12\x06bdk.v1\x1a$bdk/v1/requests/authentication.proto"\x85\x01\n\x15TestConnectionRequest\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12\x18\n\x07version\x18\x02 \x01(\tR\x07version\x12>\n\x0eauthentication\x18\x03 \x01(\x0b2\x16.bdk.v1.AuthenticationR\x0eauthenticationB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.requests.test_connection_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_TESTCONNECTIONREQUEST']._serialized_start = 88
    _globals['_TESTCONNECTIONREQUEST']._serialized_end = 221