"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,bdk/v2/requests/remove_book_connection.proto\x12\x06bdk.v2"\x82\x01\n\x1bRemoveBookConnectionRequest\x12#\n\rconnection_id\x18\x01 \x01(\tR\x0cconnectionId\x12\x1b\n\tbook_name\x18\x02 \x01(\tR\x08bookName\x12!\n\x0cbook_version\x18\x03 \x01(\tR\x0bbookVersionB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.requests.remove_book_connection_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_REMOVEBOOKCONNECTIONREQUEST']._serialized_start = 57
    _globals['_REMOVEBOOKCONNECTIONREQUEST']._serialized_end = 187