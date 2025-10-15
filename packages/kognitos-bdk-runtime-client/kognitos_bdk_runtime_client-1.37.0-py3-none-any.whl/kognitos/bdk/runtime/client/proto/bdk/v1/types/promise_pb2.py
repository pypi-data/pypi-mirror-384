"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v1.types import value_pb2 as bdk_dot_v1_dot_types_dot_value__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1abdk/v1/types/promise.proto\x12\x06bdk.v1\x1a\x18bdk/v1/types/value.proto"q\n\x07Promise\x12C\n\x1epromise_resolver_function_name\x18\x01 \x01(\tR\x1bpromiseResolverFunctionName\x12!\n\x04data\x18\x02 \x01(\x0b2\r.bdk.v1.ValueR\x04dataB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v1.types.promise_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_PROMISE']._serialized_start = 64
    _globals['_PROMISE']._serialized_end = 177