"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.responses import promise_pb2 as bdk_dot_v2_dot_responses_dot_promise__pb2
from ....bdk.v2.responses import question_pb2 as bdk_dot_v2_dot_responses_dot_question__pb2
from ....bdk.v2.types import concept_value_pb2 as bdk_dot_v2_dot_types_dot_concept__value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\'bdk/v2/responses/invoke_procedure.proto\x12\x06bdk.v2\x1a\x1ebdk/v2/responses/promise.proto\x1a\x1fbdk/v2/responses/question.proto\x1a bdk/v2/types/concept_value.proto"X\n\x17InvokeProcedureResponse\x12=\n\x0foutput_concepts\x18\x01 \x03(\x0b2\x14.bdk.v2.ConceptValueR\x0eoutputConcepts"\xe1\x01\n\x19InvokeProcedureResponseV2\x12=\n\x08response\x18\x01 \x01(\x0b2\x1f.bdk.v2.InvokeProcedureResponseH\x00R\x08response\x126\n\x08question\x18\x02 \x01(\x0b2\x18.bdk.v2.QuestionResponseH\x00R\x08question\x123\n\x07promise\x18\x03 \x01(\x0b2\x17.bdk.v2.PromiseResponseH\x00R\x07promiseB\x18\n\x16response_discriminatorB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.responses.invoke_procedure_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_INVOKEPROCEDURERESPONSE']._serialized_start = 150
    _globals['_INVOKEPROCEDURERESPONSE']._serialized_end = 238
    _globals['_INVOKEPROCEDURERESPONSEV2']._serialized_start = 241
    _globals['_INVOKEPROCEDURERESPONSEV2']._serialized_end = 466