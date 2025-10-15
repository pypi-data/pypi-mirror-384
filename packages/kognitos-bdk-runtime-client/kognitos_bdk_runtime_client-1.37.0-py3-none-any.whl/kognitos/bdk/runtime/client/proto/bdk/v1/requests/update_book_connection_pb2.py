"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.requests import authentication_pb2 as bdk_dot_v1_dot_requests_dot_authentication__pb2
from ....bdk.v1.requests import labels_pb2 as bdk_dot_v1_dot_requests_dot_labels__pb2
from ....bdk.v1.types import config_value_pb2 as bdk_dot_v1_dot_types_dot_config__value__pb2
from ....bdk.v1.types import oauth_flow_pb2 as bdk_dot_v1_dot_types_dot_oauth__flow__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,bdk/v1/requests/update_book_connection.proto\x12\x06bdk.v1\x1a$bdk/v1/requests/authentication.proto\x1a\x1cbdk/v1/requests/labels.proto\x1a\x1fbdk/v1/types/config_value.proto\x1a\x1dbdk/v1/types/oauth_flow.proto"\xdc\x02\n\x1bUpdateBookConnectionRequest\x12\x1b\n\tbook_name\x18\x01 \x01(\tR\x08bookName\x12!\n\x0cbook_version\x18\x02 \x01(\tR\x0bbookVersion\x12#\n\rconnection_id\x18\x03 \x01(\tR\x0cconnectionId\x12>\n\x0eauthentication\x18\x04 \x01(\x0b2\x16.bdk.v1.AuthenticationR\x0eauthentication\x12+\n\x06config\x18\x05 \x03(\x0b2\x13.bdk.v1.ConfigValueR\x06config\x12%\n\x06labels\x18\x06 \x03(\x0b2\r.bdk.v1.LabelR\x06labels\x125\n\noauth_flow\x18\x07 \x01(\x0e2\x11.bdk.v1.OAuthFlowH\x00R\toauthFlow\x88\x01\x01B\r\n\x0b_oauth_flowB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.requests.update_book_connection_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_UPDATEBOOKCONNECTIONREQUEST']._serialized_start = 189
    _globals['_UPDATEBOOKCONNECTIONREQUEST']._serialized_end = 537