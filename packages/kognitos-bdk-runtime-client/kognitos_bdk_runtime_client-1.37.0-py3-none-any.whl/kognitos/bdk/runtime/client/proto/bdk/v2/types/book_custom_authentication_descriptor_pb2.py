"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import credential_descriptor_pb2 as bdk_dot_v2_dot_types_dot_credential__descriptor__pb2
from ....bdk.v2.types import noun_phrase_pb2 as bdk_dot_v2_dot_types_dot_noun__phrase__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n8bdk/v2/types/book_custom_authentication_descriptor.proto\x12\x06bdk.v2\x1a(bdk/v2/types/credential_descriptor.proto\x1a\x1ebdk/v2/types/noun_phrase.proto"\xf4\x01\n"BookCustomAuthenticationDescriptor\x12\x0e\n\x02id\x18\x01 \x01(\tR\x02id\x12>\n\x0bcredentials\x18\x02 \x03(\x0b2\x1c.bdk.v2.CredentialDescriptorR\x0bcredentials\x12 \n\x0bdescription\x18\x03 \x01(\tR\x0bdescription\x12\x12\n\x04name\x18\x04 \x01(\tR\x04name\x128\n\x0bnoun_phrase\x18\x05 \x01(\x0b2\x12.bdk.v2.NounPhraseH\x00R\nnounPhrase\x88\x01\x01B\x0e\n\x0c_noun_phraseB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.book_custom_authentication_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKCUSTOMAUTHENTICATIONDESCRIPTOR']._serialized_start = 143
    _globals['_BOOKCUSTOMAUTHENTICATIONDESCRIPTOR']._serialized_end = 387