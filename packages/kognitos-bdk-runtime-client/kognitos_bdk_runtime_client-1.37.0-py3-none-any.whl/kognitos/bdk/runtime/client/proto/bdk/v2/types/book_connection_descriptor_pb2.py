"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.requests import authentication_pb2 as bdk_dot_v2_dot_requests_dot_authentication__pb2
from ....bdk.v2.requests import labels_pb2 as bdk_dot_v2_dot_requests_dot_labels__pb2
from ....bdk.v2.types import config_value_pb2 as bdk_dot_v2_dot_types_dot_config__value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n-bdk/v2/types/book_connection_descriptor.proto\x12\x06bdk.v2\x1a$bdk/v2/requests/authentication.proto\x1a\x1cbdk/v2/requests/labels.proto\x1a\x1fbdk/v2/types/config_value.proto"\xf4\x02\n\x18BookConnectionDescriptor\x12\x1b\n\tbook_name\x18\x01 \x01(\tR\x08bookName\x12!\n\x0cbook_version\x18\x02 \x01(\tR\x0bbookVersion\x12#\n\rconnection_id\x18\x03 \x01(\tR\x0cconnectionId\x12>\n\x0eauthentication\x18\x04 \x01(\x0b2\x16.bdk.v2.AuthenticationR\x0eauthentication\x12+\n\x06config\x18\x05 \x03(\x0b2\x13.bdk.v2.ConfigValueR\x06config\x12%\n\x06labels\x18\x06 \x03(\x0b2\r.bdk.v2.LabelR\x06labels\x121\n\x05state\x18\x07 \x01(\x0e2\x1b.bdk.v2.BookConnectionStateR\x05state\x12\x1f\n\x08endpoint\x18\t \x01(\tH\x00R\x08endpoint\x88\x01\x01B\x0b\n\t_endpoint*{\n\x13BookConnectionState\x12!\n\x1dBOOK_CONNECTION_STATE_PENDING\x10\x00\x12\x1f\n\x1bBOOK_CONNECTION_STATE_READY\x10\x01\x12 \n\x1cBOOK_CONNECTION_STATE_FAILED\x10\x02B\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.book_connection_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKCONNECTIONSTATE']._serialized_start = 533
    _globals['_BOOKCONNECTIONSTATE']._serialized_end = 656
    _globals['_BOOKCONNECTIONDESCRIPTOR']._serialized_start = 159
    _globals['_BOOKCONNECTIONDESCRIPTOR']._serialized_end = 531