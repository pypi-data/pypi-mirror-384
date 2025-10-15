"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import noun_phrase_pb2 as bdk_dot_v2_dot_types_dot_noun__phrase__pb2
from ....bdk.v2.types import value_pb2 as bdk_dot_v2_dot_types_dot_value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n bdk/v2/types/concept_value.proto\x12\x06bdk.v2\x1a\x1ebdk/v2/types/noun_phrase.proto\x1a\x18bdk/v2/types/value.proto"k\n\x0cConceptValue\x126\n\x0cnoun_phrases\x18\x01 \x01(\x0b2\x13.bdk.v2.NounPhrasesR\x0bnounPhrases\x12#\n\x05value\x18\x02 \x01(\x0b2\r.bdk.v2.ValueR\x05valueB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.concept_value_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_CONCEPTVALUE']._serialized_start = 102
    _globals['_CONCEPTVALUE']._serialized_end = 209