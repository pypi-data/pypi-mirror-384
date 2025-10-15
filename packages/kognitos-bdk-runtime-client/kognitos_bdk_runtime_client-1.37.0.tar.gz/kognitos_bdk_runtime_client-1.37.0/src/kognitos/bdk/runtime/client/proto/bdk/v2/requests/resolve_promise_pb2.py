"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.requests import authentication_pb2 as bdk_dot_v2_dot_requests_dot_authentication__pb2
from ....bdk.v2.requests import offload_pb2 as bdk_dot_v2_dot_requests_dot_offload__pb2
from ....bdk.v2.types import answered_question_pb2 as bdk_dot_v2_dot_types_dot_answered__question__pb2
from ....bdk.v2.types import concept_value_pb2 as bdk_dot_v2_dot_types_dot_concept__value__pb2
from ....bdk.v2.types import promise_pb2 as bdk_dot_v2_dot_types_dot_promise__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%bdk/v2/requests/resolve_promise.proto\x12\x06bdk.v2\x1a$bdk/v2/requests/authentication.proto\x1a\x1dbdk/v2/requests/offload.proto\x1a$bdk/v2/types/answered_question.proto\x1a bdk/v2/types/concept_value.proto\x1a\x1abdk/v2/types/promise.proto"\x96\x03\n\x15ResolvePromiseRequest\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12\x18\n\x07version\x18\x02 \x01(\tR\x07version\x12>\n\x0eauthentication\x18\x03 \x01(\x0b2\x16.bdk.v2.AuthenticationR\x0eauthentication\x12!\n\x0cprocedure_id\x18\x04 \x01(\tR\x0bprocedureId\x12)\n\x07promise\x18\x05 \x01(\x0b2\x0f.bdk.v2.PromiseR\x07promise\x12.\n\x07offload\x18\x06 \x01(\x0b2\x0f.bdk.v2.OffloadH\x00R\x07offload\x88\x01\x01\x12G\n\x12answered_questions\x18\x07 \x03(\x0b2\x18.bdk.v2.AnsweredQuestionR\x11answeredQuestions\x12<\n\x0econfigurations\x18\x08 \x03(\x0b2\x14.bdk.v2.ConceptValueR\x0econfigurationsB\n\n\x08_offloadB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.requests.resolve_promise_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RESOLVEPROMISEREQUEST']._serialized_start = 219
    _globals['_RESOLVEPROMISEREQUEST']._serialized_end = 625