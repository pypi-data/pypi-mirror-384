"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import user_info_pb2 as bdk_dot_v2_dot_types_dot_user__info__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n)bdk/v2/responses/retrieve_user_info.proto\x12\x06bdk.v2\x1a\x1cbdk/v2/types/user_info.proto"I\n\x18RetrieveUserInfoResponse\x12-\n\tuser_info\x18\x01 \x01(\x0b2\x10.bdk.v2.UserInfoR\x08userInfoB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.responses.retrieve_user_info_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RETRIEVEUSERINFORESPONSE']._serialized_start = 83
    _globals['_RETRIEVEUSERINFORESPONSE']._serialized_end = 156