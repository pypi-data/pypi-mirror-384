"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import credential_type_pb2 as bdk_dot_v2_dot_types_dot_credential__type__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(bdk/v2/types/credential_descriptor.proto\x12\x06bdk.v2\x1a"bdk/v2/types/credential_type.proto"\xc8\x01\n\x14CredentialDescriptor\x12\x0e\n\x02id\x18\x01 \x01(\tR\x02id\x12*\n\x04type\x18\x02 \x01(\x0e2\x16.bdk.v2.CredentialTypeR\x04type\x12\x19\n\x05label\x18\x03 \x01(\tH\x00R\x05label\x88\x01\x01\x12\x18\n\x07visible\x18\x04 \x01(\x08R\x07visible\x12%\n\x0bdescription\x18\x05 \x01(\tH\x01R\x0bdescription\x88\x01\x01B\x08\n\x06_labelB\x0e\n\x0c_descriptionB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.credential_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_CREDENTIALDESCRIPTOR']._serialized_start = 89
    _globals['_CREDENTIALDESCRIPTOR']._serialized_end = 289