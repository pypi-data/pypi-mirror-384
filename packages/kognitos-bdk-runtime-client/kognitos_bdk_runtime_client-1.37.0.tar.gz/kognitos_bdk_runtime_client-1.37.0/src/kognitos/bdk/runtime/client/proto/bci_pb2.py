"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from .bdk.v1 import v1_pb2 as bdk_dot_v1_dot_v1__pb2
from .bdk.v2 import v2_pb2 as bdk_dot_v2_dot_v2__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2
from .grpc.health.v1 import health_pb2 as grpc_dot_health_dot_v1_dot_health__pb2
from . import version_pb2 as version__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tbci.proto\x12\x03bdk\x1a\x0fbdk/v1/v1.proto\x1a\x0fbdk/v2/v2.proto\x1a\x1cgoogle/protobuf/struct.proto\x1a\x1bgrpc/health/v1/health.proto\x1a\rversion.protoB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bci_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'