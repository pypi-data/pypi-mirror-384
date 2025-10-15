"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.requests import context_pb2 as bdk_dot_v2_dot_requests_dot_context__pb2
from ....bdk.v2.requests import discover_procedures_pb2 as bdk_dot_v2_dot_requests_dot_discover__procedures__pb2
from ....bdk.v2.requests import environment_information_pb2 as bdk_dot_v2_dot_requests_dot_environment__information__pb2
from ....bdk.v2.requests import invoke_procedure_pb2 as bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2
from ....bdk.v2.requests import resolve_promise_pb2 as bdk_dot_v2_dot_requests_dot_resolve__promise__pb2
from ....bdk.v2.requests import retrieve_book_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__pb2
from ....bdk.v2.requests import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2
from ....bdk.v2.requests import retrieve_books_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__pb2
from ....bdk.v2.requests import retrieve_discoverables_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__discoverables__pb2
from ....bdk.v2.requests import retrieve_tags_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2
from ....bdk.v2.requests import retrieve_user_info_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__user__info__pb2
from ....bdk.v2.requests import test_connection_pb2 as bdk_dot_v2_dot_requests_dot_test__connection__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dbdk/v2/requests/request.proto\x12\x06bdk.v2\x1a\x1dbdk/v2/requests/context.proto\x1a)bdk/v2/requests/discover_procedures.proto\x1a-bdk/v2/requests/environment_information.proto\x1a&bdk/v2/requests/invoke_procedure.proto\x1a%bdk/v2/requests/resolve_promise.proto\x1a#bdk/v2/requests/retrieve_book.proto\x1a.bdk/v2/requests/retrieve_book_procedures.proto\x1a$bdk/v2/requests/retrieve_books.proto\x1a,bdk/v2/requests/retrieve_discoverables.proto\x1a#bdk/v2/requests/retrieve_tags.proto\x1a(bdk/v2/requests/retrieve_user_info.proto\x1a%bdk/v2/requests/test_connection.proto"\xbf\x07\n\x07Request\x12)\n\x07context\x18\x01 \x01(\x0b2\x0f.bdk.v2.ContextR\x07context\x12`\n\x17environment_information\x18\x02 \x01(\x0b2%.bdk.v2.EnvironmentInformationRequestH\x00R\x16environmentInformation\x12E\n\x0eretrieve_books\x18\x03 \x01(\x0b2\x1c.bdk.v2.RetrieveBooksRequestH\x00R\rretrieveBooks\x12B\n\rretrieve_book\x18\x04 \x01(\x0b2\x1b.bdk.v2.RetrieveBookRequestH\x00R\x0cretrieveBook\x12X\n\x13retrieve_procedures\x18\x05 \x01(\x0b2%.bdk.v2.RetrieveBookProceduresRequestH\x00R\x12retrieveProcedures\x12H\n\x0ftest_connection\x18\x06 \x01(\x0b2\x1d.bdk.v2.TestConnectionRequestH\x00R\x0etestConnection\x12K\n\x10invoke_procedure\x18\x07 \x01(\x0b2\x1e.bdk.v2.InvokeProcedureRequestH\x00R\x0finvokeProcedure\x12T\n\x13discover_procedures\x18\x08 \x01(\x0b2!.bdk.v2.DiscoverProceduresRequestH\x00R\x12discoverProcedures\x12]\n\x16retrieve_discoverables\x18\t \x01(\x0b2$.bdk.v2.RetrieveDiscoverablesRequestH\x00R\x15retrieveDiscoverables\x12B\n\rretrieve_tags\x18\n \x01(\x0b2\x1b.bdk.v2.RetrieveTagsRequestH\x00R\x0cretrieveTags\x12H\n\x0fresolve_promise\x18\x0b \x01(\x0b2\x1d.bdk.v2.ResolvePromiseRequestH\x00R\x0eresolvePromise\x12O\n\x12retrieve_user_info\x18\x0c \x01(\x0b2\x1f.bdk.v2.RetrieveUserInfoRequestH\x00R\x10retrieveUserInfoB\x17\n\x15request_discriminatorB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.requests.request_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_REQUEST']._serialized_start = 529
    _globals['_REQUEST']._serialized_end = 1488