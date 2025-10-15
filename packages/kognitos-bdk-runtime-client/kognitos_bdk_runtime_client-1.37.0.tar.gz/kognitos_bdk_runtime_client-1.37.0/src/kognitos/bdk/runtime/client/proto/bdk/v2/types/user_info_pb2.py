"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cbdk/v2/types/user_info.proto\x12\x06bdk.v2"\xf3\x01\n\x08UserInfo\x12\x19\n\x05email\x18\x01 \x01(\tH\x00R\x05email\x88\x01\x01\x12\x1f\n\x08username\x18\x02 \x01(\tH\x01R\x08username\x88\x01\x01\x12P\n\x10other_attributes\x18\x03 \x03(\x0b2%.bdk.v2.UserInfo.OtherAttributesEntryR\x0fotherAttributes\x1aB\n\x14OtherAttributesEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12\x14\n\x05value\x18\x02 \x01(\tR\x05value:\x028\x01B\x08\n\x06_emailB\x0b\n\t_usernameB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.user_info_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_USERINFO_OTHERATTRIBUTESENTRY']._options = None
    _globals['_USERINFO_OTHERATTRIBUTESENTRY']._serialized_options = b'8\x01'
    _globals['_USERINFO']._serialized_start = 41
    _globals['_USERINFO']._serialized_end = 284
    _globals['_USERINFO_OTHERATTRIBUTESENTRY']._serialized_start = 195
    _globals['_USERINFO_OTHERATTRIBUTESENTRY']._serialized_end = 261