"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import concept_type_pb2 as bdk_dot_v1_dot_types_dot_concept__type__pb2
from ....bdk.v1.types import noun_phrase_pb2 as bdk_dot_v1_dot_types_dot_noun__phrase__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&bdk/v1/types/question_descriptor.proto\x12\x06bdk.v1\x1a\x1fbdk/v1/types/concept_type.proto\x1a\x1ebdk/v1/types/noun_phrase.proto"u\n\x12QuestionDescriptor\x126\n\x0cnoun_phrases\x18\x01 \x01(\x0b2\x13.bdk.v1.NounPhrasesR\x0bnounPhrases\x12\'\n\x04type\x18\x02 \x01(\x0b2\x13.bdk.v1.ConceptTypeR\x04typeB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.types.question_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_QUESTIONDESCRIPTOR']._serialized_start = 115
    _globals['_QUESTIONDESCRIPTOR']._serialized_end = 232