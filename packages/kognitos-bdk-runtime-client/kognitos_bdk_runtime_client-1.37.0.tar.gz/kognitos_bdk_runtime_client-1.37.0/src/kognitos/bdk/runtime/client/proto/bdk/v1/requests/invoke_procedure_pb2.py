"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.requests import authentication_pb2 as bdk_dot_v1_dot_requests_dot_authentication__pb2
from ....bdk.v1.requests import offload_pb2 as bdk_dot_v1_dot_requests_dot_offload__pb2
from ....bdk.v1.types import answered_question_pb2 as bdk_dot_v1_dot_types_dot_answered__question__pb2
from ....bdk.v1.types import concept_value_pb2 as bdk_dot_v1_dot_types_dot_concept__value__pb2
from ....bdk.v1.types import expression_pb2 as bdk_dot_v1_dot_types_dot_expression__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&bdk/v1/requests/invoke_procedure.proto\x12\x06bdk.v1\x1a$bdk/v1/requests/authentication.proto\x1a\x1dbdk/v1/requests/offload.proto\x1a$bdk/v1/types/answered_question.proto\x1a bdk/v1/types/concept_value.proto\x1a\x1dbdk/v1/types/expression.proto"\x94\x04\n\x16InvokeProcedureRequest\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12\x18\n\x07version\x18\x02 \x01(\tR\x07version\x12>\n\x0eauthentication\x18\x03 \x01(\x0b2\x16.bdk.v1.AuthenticationR\x0eauthentication\x12!\n\x0cprocedure_id\x18\x04 \x01(\tR\x0bprocedureId\x12;\n\x0einput_concepts\x18\x05 \x03(\x0b2\x14.bdk.v1.ConceptValueR\rinputConcepts\x12D\n\x11filter_expression\x18\x06 \x01(\x0b2\x12.bdk.v1.ExpressionH\x00R\x10filterExpression\x88\x01\x01\x12.\n\x07offload\x18\x07 \x01(\x0b2\x0f.bdk.v1.OffloadH\x01R\x07offload\x88\x01\x01\x12\x1b\n\x06offset\x18\x08 \x01(\x04H\x02R\x06offset\x88\x01\x01\x12\x19\n\x05limit\x18\t \x01(\x04H\x03R\x05limit\x88\x01\x01\x12G\n\x12answered_questions\x18\n \x03(\x0b2\x18.bdk.v1.AnsweredQuestionR\x11answeredQuestionsB\x14\n\x12_filter_expressionB\n\n\x08_offloadB\t\n\x07_offsetB\x08\n\x06_limitB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.requests.invoke_procedure_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_INVOKEPROCEDUREREQUEST']._serialized_start = 223
    _globals['_INVOKEPROCEDUREREQUEST']._serialized_end = 755