"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.types import book_procedure_signature_pb2 as bdk_dot_v2_dot_types_dot_book__procedure__signature__pb2
from ....bdk.v2.types import concept_descriptor_pb2 as bdk_dot_v2_dot_types_dot_concept__descriptor__pb2
from ....bdk.v2.types import connection_required_pb2 as bdk_dot_v2_dot_types_dot_connection__required__pb2
from ....bdk.v2.types import example_descriptor_pb2 as bdk_dot_v2_dot_types_dot_example__descriptor__pb2
from ....bdk.v2.types import question_descriptor_pb2 as bdk_dot_v2_dot_types_dot_question__descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,bdk/v2/types/book_procedure_descriptor.proto\x12\x06bdk.v2\x1a+bdk/v2/types/book_procedure_signature.proto\x1a%bdk/v2/types/concept_descriptor.proto\x1a&bdk/v2/types/connection_required.proto\x1a%bdk/v2/types/example_descriptor.proto\x1a&bdk/v2/types/question_descriptor.proto"\x8b\x06\n\x17BookProcedureDescriptor\x12\x0e\n\x02id\x18\x01 \x01(\tR\x02id\x12<\n\tsignature\x18\x02 \x01(\x0b2\x1e.bdk.v2.BookProcedureSignatureR\tsignature\x121\n\x06inputs\x18\x03 \x03(\x0b2\x19.bdk.v2.ConceptDescriptorR\x06inputs\x123\n\x07outputs\x18\x04 \x03(\x0b2\x19.bdk.v2.ConceptDescriptorR\x07outputs\x120\n\x11short_description\x18\x05 \x01(\tH\x00R\x10shortDescription\x88\x01\x01\x12.\n\x10long_description\x18\x06 \x01(\tH\x01R\x0flongDescription\x88\x01\x01\x12%\n\x0efilter_capable\x18\x07 \x01(\x08R\rfilterCapable\x12!\n\x0cpage_capable\x18\x08 \x01(\x08R\x0bpageCapable\x123\n\x13connection_required\x18\t \x01(\x08B\x02\x18\x01R\x12connectionRequired\x12#\n\ris_discovered\x18\n \x01(\x08R\x0cisDiscovered\x128\n\tquestions\x18\x0b \x03(\x0b2\x1a.bdk.v2.QuestionDescriptorR\tquestions\x125\n\x08examples\x18\x0c \x03(\x0b2\x19.bdk.v2.ExampleDescriptorR\x08examples\x12\x19\n\x08is_async\x18\r \x01(\x08R\x07isAsync\x12\\\n\x1cconnection_requirement_level\x18\x0e \x01(\x0e2\x1a.bdk.v2.ConnectionRequiredR\x1aconnectionRequirementLevel\x12\x1f\n\x0bis_mutation\x18\x0f \x01(\x08R\nisMutationB\x14\n\x12_short_descriptionB\x13\n\x11_long_description"\xc7\x05\n\x19BookProcedureDescriptorV2\x12\x0e\n\x02id\x18\x01 \x01(\tR\x02id\x12<\n\tsignature\x18\x02 \x01(\x0b2\x1e.bdk.v2.BookProcedureSignatureR\tsignature\x121\n\x06inputs\x18\x03 \x03(\x0b2\x19.bdk.v2.ConceptDescriptorR\x06inputs\x123\n\x07outputs\x18\x04 \x03(\x0b2\x19.bdk.v2.ConceptDescriptorR\x07outputs\x120\n\x11short_description\x18\x05 \x01(\tH\x00R\x10shortDescription\x88\x01\x01\x12.\n\x10long_description\x18\x06 \x01(\tH\x01R\x0flongDescription\x88\x01\x01\x12%\n\x0efilter_capable\x18\x07 \x01(\x08R\rfilterCapable\x12!\n\x0cpage_capable\x18\x08 \x01(\x08R\x0bpageCapable\x12K\n\x13connection_required\x18\t \x01(\x0e2\x1a.bdk.v2.ConnectionRequiredR\x12connectionRequired\x12#\n\ris_discovered\x18\n \x01(\x08R\x0cisDiscovered\x128\n\tquestions\x18\x0b \x03(\x0b2\x1a.bdk.v2.QuestionDescriptorR\tquestions\x125\n\x08examples\x18\x0c \x03(\x0b2\x19.bdk.v2.ExampleDescriptorR\x08examples\x12\x19\n\x08is_async\x18\r \x01(\x08R\x07isAsync\x12\x1f\n\x0bis_mutation\x18\x0e \x01(\x08R\nisMutationB\x14\n\x12_short_descriptionB\x13\n\x11_long_descriptionB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.types.book_procedure_descriptor_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKPROCEDUREDESCRIPTOR'].fields_by_name['connection_required']._options = None
    _globals['_BOOKPROCEDUREDESCRIPTOR'].fields_by_name['connection_required']._serialized_options = b'\x18\x01'
    _globals['_BOOKPROCEDUREDESCRIPTOR']._serialized_start = 260
    _globals['_BOOKPROCEDUREDESCRIPTOR']._serialized_end = 1039
    _globals['_BOOKPROCEDUREDESCRIPTORV2']._serialized_start = 1042
    _globals['_BOOKPROCEDUREDESCRIPTORV2']._serialized_end = 1753