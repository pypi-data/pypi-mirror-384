"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$bdk/v2/requests/retrieve_books.proto\x12\x06bdk.v2"y\n\x14RetrieveBooksRequest\x12 \n\tpage_size\x18\x01 \x01(\rH\x00R\x08pageSize\x88\x01\x01\x12"\n\npage_token\x18\x02 \x01(\tH\x01R\tpageToken\x88\x01\x01B\x0c\n\n_page_sizeB\r\n\x0b_page_tokenB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.requests.retrieve_books_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_RETRIEVEBOOKSREQUEST']._serialized_start = 48
    _globals['_RETRIEVEBOOKSREQUEST']._serialized_end = 169