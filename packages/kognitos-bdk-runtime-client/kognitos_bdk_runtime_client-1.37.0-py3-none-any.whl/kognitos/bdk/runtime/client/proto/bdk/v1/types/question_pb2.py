"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import concept_type_pb2 as bdk_dot_v1_dot_types_dot_concept__type__pb2
from ....bdk.v1.types import noun_phrase_pb2 as bdk_dot_v1_dot_types_dot_noun__phrase__pb2
from ....bdk.v1.types import value_pb2 as bdk_dot_v1_dot_types_dot_value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1bbdk/v1/types/question.proto\x12\x06bdk.v1\x1a\x1fbdk/v1/types/concept_type.proto\x1a\x1ebdk/v1/types/noun_phrase.proto\x1a\x18bdk/v1/types/value.proto"\xc5\x01\n\x08Question\x126\n\x0cnoun_phrases\x18\x01 \x01(\x0b2\x13.bdk.v1.NounPhrasesR\x0bnounPhrases\x126\n\x0cconcept_type\x18\x02 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x0bconceptType\x12\'\n\x07choices\x18\x03 \x03(\x0b2\r.bdk.v1.ValueR\x07choices\x12\x17\n\x04text\x18\x04 \x01(\tH\x00R\x04text\x88\x01\x01B\x07\n\x05_textB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.types.question_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_QUESTION']._serialized_start = 131
    _globals['_QUESTION']._serialized_end = 328