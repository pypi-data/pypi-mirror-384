"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.requests import discover_procedures_pb2 as bdk_dot_v2_dot_requests_dot_discover__procedures__pb2
from ....bdk.v2.requests import environment_information_pb2 as bdk_dot_v2_dot_requests_dot_environment__information__pb2
from ....bdk.v2.requests import invoke_procedure_pb2 as bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2
from ....bdk.v2.requests import resolve_promise_pb2 as bdk_dot_v2_dot_requests_dot_resolve__promise__pb2
from ....bdk.v2.requests import retrieve_book_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__pb2
from ....bdk.v2.requests import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2
from ....bdk.v2.requests import retrieve_books_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__pb2
from ....bdk.v2.requests import retrieve_discoverables_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__discoverables__pb2
from ....bdk.v2.requests import retrieve_user_info_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__user__info__pb2
from ....bdk.v2.requests import test_connection_pb2 as bdk_dot_v2_dot_requests_dot_test__connection__pb2
from ....bdk.v2.responses import discover_procedures_pb2 as bdk_dot_v2_dot_responses_dot_discover__procedures__pb2
from ....bdk.v2.responses import environment_information_pb2 as bdk_dot_v2_dot_responses_dot_environment__information__pb2
from ....bdk.v2.responses import invoke_procedure_pb2 as bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2
from ....bdk.v2.responses import retrieve_book_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__pb2
from ....bdk.v2.responses import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2
from ....bdk.v2.responses import retrieve_books_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__books__pb2
from ....bdk.v2.responses import retrieve_discoverables_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__discoverables__pb2
from ....bdk.v2.responses import retrieve_user_info_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__user__info__pb2
from ....bdk.v2.responses import test_connection_pb2 as bdk_dot_v2_dot_responses_dot_test__connection__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1abdk/v2/services/book.proto\x12\x06bdk.v2\x1a)bdk/v2/requests/discover_procedures.proto\x1a-bdk/v2/requests/environment_information.proto\x1a&bdk/v2/requests/invoke_procedure.proto\x1a%bdk/v2/requests/resolve_promise.proto\x1a#bdk/v2/requests/retrieve_book.proto\x1a.bdk/v2/requests/retrieve_book_procedures.proto\x1a$bdk/v2/requests/retrieve_books.proto\x1a,bdk/v2/requests/retrieve_discoverables.proto\x1a(bdk/v2/requests/retrieve_user_info.proto\x1a%bdk/v2/requests/test_connection.proto\x1a*bdk/v2/responses/discover_procedures.proto\x1a.bdk/v2/responses/environment_information.proto\x1a\'bdk/v2/responses/invoke_procedure.proto\x1a$bdk/v2/responses/retrieve_book.proto\x1a/bdk/v2/responses/retrieve_book_procedures.proto\x1a%bdk/v2/responses/retrieve_books.proto\x1a-bdk/v2/responses/retrieve_discoverables.proto\x1a)bdk/v2/responses/retrieve_user_info.proto\x1a&bdk/v2/responses/test_connection.proto2\x8f\x07\n\x0bBookService\x12g\n\x16EnvironmentInformation\x12%.bdk.v2.EnvironmentInformationRequest\x1a&.bdk.v2.EnvironmentInformationResponse\x12L\n\rRetrieveBooks\x12\x1c.bdk.v2.RetrieveBooksRequest\x1a\x1d.bdk.v2.RetrieveBooksResponse\x12I\n\x0cRetrieveBook\x12\x1b.bdk.v2.RetrieveBookRequest\x1a\x1c.bdk.v2.RetrieveBookResponse\x12i\n\x16RetrieveBookProcedures\x12%.bdk.v2.RetrieveBookProceduresRequest\x1a(.bdk.v2.RetrieveBookProceduresResponseV2\x12O\n\x0eTestConnection\x12\x1d.bdk.v2.TestConnectionRequest\x1a\x1e.bdk.v2.TestConnectionResponse\x12T\n\x0fInvokeProcedure\x12\x1e.bdk.v2.InvokeProcedureRequest\x1a!.bdk.v2.InvokeProcedureResponseV2\x12[\n\x12DiscoverProcedures\x12!.bdk.v2.DiscoverProceduresRequest\x1a".bdk.v2.DiscoverProceduresResponse\x12d\n\x15RetrieveDiscoverables\x12$.bdk.v2.RetrieveDiscoverablesRequest\x1a%.bdk.v2.RetrieveDiscoverablesResponse\x12R\n\x0eResolvePromise\x12\x1d.bdk.v2.ResolvePromiseRequest\x1a!.bdk.v2.InvokeProcedureResponseV2\x12U\n\x10RetrieveUserInfo\x12\x1f.bdk.v2.RetrieveUserInfoRequest\x1a .bdk.v2.RetrieveUserInfoResponseB\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.services.book_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_BOOKSERVICE']._serialized_start = 847
    _globals['_BOOKSERVICE']._serialized_end = 1758