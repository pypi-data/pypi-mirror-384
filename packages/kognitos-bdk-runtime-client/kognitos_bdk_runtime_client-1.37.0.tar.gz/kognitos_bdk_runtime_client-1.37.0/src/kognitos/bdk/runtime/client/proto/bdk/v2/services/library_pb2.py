"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from ....bdk.v2.requests import add_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_add__book__connection__pb2
from ....bdk.v2.requests import book_connection_oauth_callback_pb2 as bdk_dot_v2_dot_requests_dot_book__connection__oauth__callback__pb2
from ....bdk.v2.requests import discover_procedures_pb2 as bdk_dot_v2_dot_requests_dot_discover__procedures__pb2
from ....bdk.v2.requests import environment_information_pb2 as bdk_dot_v2_dot_requests_dot_environment__information__pb2
from ....bdk.v2.requests import invoke_procedure_pb2 as bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2
from ....bdk.v2.requests import remove_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_remove__book__connection__pb2
from ....bdk.v2.requests import retrieve_book_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__pb2
from ....bdk.v2.requests import retrieve_book_connections_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__connections__pb2
from ....bdk.v2.requests import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2
from ....bdk.v2.requests import retrieve_books_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__pb2
from ....bdk.v2.requests import retrieve_books_connections_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__connections__pb2
from ....bdk.v2.requests import retrieve_tags_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2
from ....bdk.v2.requests import test_connection_pb2 as bdk_dot_v2_dot_requests_dot_test__connection__pb2
from ....bdk.v2.requests import update_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_update__book__connection__pb2
from ....bdk.v2.requests import upgrade_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_upgrade__book__connection__pb2
from ....bdk.v2.responses import book_connection_pb2 as bdk_dot_v2_dot_responses_dot_book__connection__pb2
from ....bdk.v2.responses import discover_procedures_pb2 as bdk_dot_v2_dot_responses_dot_discover__procedures__pb2
from ....bdk.v2.responses import environment_information_pb2 as bdk_dot_v2_dot_responses_dot_environment__information__pb2
from ....bdk.v2.responses import invoke_procedure_pb2 as bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2
from ....bdk.v2.responses import remove_book_connection_pb2 as bdk_dot_v2_dot_responses_dot_remove__book__connection__pb2
from ....bdk.v2.responses import retrieve_book_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__pb2
from ....bdk.v2.responses import retrieve_book_connections_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__connections__pb2
from ....bdk.v2.responses import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2
from ....bdk.v2.responses import retrieve_books_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__books__pb2
from ....bdk.v2.responses import retrieve_books_connections_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__books__connections__pb2
from ....bdk.v2.responses import retrieve_tags_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__tags__pb2
from ....bdk.v2.responses import test_connection_pb2 as bdk_dot_v2_dot_responses_dot_test__connection__pb2
from ....bdk.v2.responses import upgrade_book_connection_pb2 as bdk_dot_v2_dot_responses_dot_upgrade__book__connection__pb2
from ....google.api import annotations_pb2 as google_dot_api_dot_annotations__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dbdk/v2/services/library.proto\x12\x06bdk.v2\x1a)bdk/v2/requests/add_book_connection.proto\x1a4bdk/v2/requests/book_connection_oauth_callback.proto\x1a)bdk/v2/requests/discover_procedures.proto\x1a-bdk/v2/requests/environment_information.proto\x1a&bdk/v2/requests/invoke_procedure.proto\x1a,bdk/v2/requests/remove_book_connection.proto\x1a#bdk/v2/requests/retrieve_book.proto\x1a/bdk/v2/requests/retrieve_book_connections.proto\x1a.bdk/v2/requests/retrieve_book_procedures.proto\x1a$bdk/v2/requests/retrieve_books.proto\x1a0bdk/v2/requests/retrieve_books_connections.proto\x1a#bdk/v2/requests/retrieve_tags.proto\x1a%bdk/v2/requests/test_connection.proto\x1a,bdk/v2/requests/update_book_connection.proto\x1a-bdk/v2/requests/upgrade_book_connection.proto\x1a&bdk/v2/responses/book_connection.proto\x1a*bdk/v2/responses/discover_procedures.proto\x1a.bdk/v2/responses/environment_information.proto\x1a\'bdk/v2/responses/invoke_procedure.proto\x1a-bdk/v2/responses/remove_book_connection.proto\x1a$bdk/v2/responses/retrieve_book.proto\x1a0bdk/v2/responses/retrieve_book_connections.proto\x1a/bdk/v2/responses/retrieve_book_procedures.proto\x1a%bdk/v2/responses/retrieve_books.proto\x1a1bdk/v2/responses/retrieve_books_connections.proto\x1a$bdk/v2/responses/retrieve_tags.proto\x1a&bdk/v2/responses/test_connection.proto\x1a.bdk/v2/responses/upgrade_book_connection.proto\x1a\x1cgoogle/api/annotations.proto2\x83\x0e\n\x0eLibraryService\x12c\n\rRetrieveBooks\x12\x1c.bdk.v2.RetrieveBooksRequest\x1a\x1d.bdk.v2.RetrieveBooksResponse"\x15\x82\xd3\xe4\x93\x02\x0f\x12\r/api/v1/books\x12q\n\x0cRetrieveBook\x12\x1b.bdk.v2.RetrieveBookRequest\x1a\x1c.bdk.v2.RetrieveBookResponse"&\x82\xd3\xe4\x93\x02 \x12\x1e/api/v1/books/{name}/{version}\x12\x9c\x01\n\x16RetrieveBookProcedures\x12%.bdk.v2.RetrieveBookProceduresRequest\x1a(.bdk.v2.RetrieveBookProceduresResponseV2"1\x82\xd3\xe4\x93\x02+\x12)/api/v1/books/{name}/{version}/procedures\x12\x97\x01\n\x0eTestConnection\x12\x1d.bdk.v2.TestConnectionRequest\x1a\x1e.bdk.v2.TestConnectionResponse"F\x82\xd3\xe4\x93\x02@"./api/v1/books/{name}/{version}/test-connection:\x0eauthentication\x12_\n\x0cRetrieveTags\x12\x1b.bdk.v2.RetrieveTagsRequest\x1a\x1c.bdk.v2.RetrieveTagsResponse"\x14\x82\xd3\xe4\x93\x02\x0e\x12\x0c/api/v1/tags\x12\x96\x01\n\x11AddBookConnection\x12 .bdk.v2.AddBookConnectionRequest\x1a\x1e.bdk.v2.BookConnectionResponse"?\x82\xd3\xe4\x93\x029"4/api/v1/books/{book_name}/{book_version}/connections:\x01*\x12\xac\x01\n\x14UpdateBookConnection\x12#.bdk.v2.UpdateBookConnectionRequest\x1a\x1e.bdk.v2.BookConnectionResponse"O\x82\xd3\xe4\x93\x02I\x1aD/api/v1/books/{book_name}/{book_version}/connections/{connection_id}:\x01*\x12\x8c\x01\n\x1bBookConnectionOAuthCallback\x12*.bdk.v2.BookConnectionOAuthCallbackRequest\x1a\x1e.bdk.v2.BookConnectionResponse"!\x82\xd3\xe4\x93\x02\x1b"\x16/api/v1/oauth/callback:\x01*\x12\xaf\x01\n\x14RemoveBookConnection\x12#.bdk.v2.RemoveBookConnectionRequest\x1a$.bdk.v2.RemoveBookConnectionResponse"L\x82\xd3\xe4\x93\x02F*D/api/v1/books/{book_name}/{book_version}/connections/{connection_id}\x12\xa8\x01\n\x17RetrieveBookConnections\x12&.bdk.v2.RetrieveBookConnectionsRequest\x1a\'.bdk.v2.RetrieveBookConnectionsResponse"<\x82\xd3\xe4\x93\x026\x124/api/v1/books/{book_name}/{book_version}/connections\x12\x8a\x01\n\x18RetrieveBooksConnections\x12\'.bdk.v2.RetrieveBooksConnectionsRequest\x1a(.bdk.v2.RetrieveBooksConnectionsResponse"\x1b\x82\xd3\xe4\x93\x02\x15\x12\x13/api/v1/connections\x12\xbd\x01\n\x15UpgradeBookConnection\x12$.bdk.v2.UpgradeBookConnectionRequest\x1a%.bdk.v2.UpgradeBookConnectionResponse"W\x82\xd3\xe4\x93\x02Q\x1aL/api/v1/books/{book_name}/{book_version}/connections/{connection_id}/upgrade:\x01*B\x1fZ\x1dgithub.com/kognitos/bdk-protob\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bdk.v2.services.library_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals['DESCRIPTOR']._options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1dgithub.com/kognitos/bdk-proto'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBooks']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBooks']._serialized_options = b'\x82\xd3\xe4\x93\x02\x0f\x12\r/api/v1/books'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBook']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBook']._serialized_options = b'\x82\xd3\xe4\x93\x02 \x12\x1e/api/v1/books/{name}/{version}'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBookProcedures']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBookProcedures']._serialized_options = b'\x82\xd3\xe4\x93\x02+\x12)/api/v1/books/{name}/{version}/procedures'
    _globals['_LIBRARYSERVICE'].methods_by_name['TestConnection']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['TestConnection']._serialized_options = b'\x82\xd3\xe4\x93\x02@"./api/v1/books/{name}/{version}/test-connection:\x0eauthentication'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveTags']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveTags']._serialized_options = b'\x82\xd3\xe4\x93\x02\x0e\x12\x0c/api/v1/tags'
    _globals['_LIBRARYSERVICE'].methods_by_name['AddBookConnection']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['AddBookConnection']._serialized_options = b'\x82\xd3\xe4\x93\x029"4/api/v1/books/{book_name}/{book_version}/connections:\x01*'
    _globals['_LIBRARYSERVICE'].methods_by_name['UpdateBookConnection']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['UpdateBookConnection']._serialized_options = b'\x82\xd3\xe4\x93\x02I\x1aD/api/v1/books/{book_name}/{book_version}/connections/{connection_id}:\x01*'
    _globals['_LIBRARYSERVICE'].methods_by_name['BookConnectionOAuthCallback']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['BookConnectionOAuthCallback']._serialized_options = b'\x82\xd3\xe4\x93\x02\x1b"\x16/api/v1/oauth/callback:\x01*'
    _globals['_LIBRARYSERVICE'].methods_by_name['RemoveBookConnection']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RemoveBookConnection']._serialized_options = b'\x82\xd3\xe4\x93\x02F*D/api/v1/books/{book_name}/{book_version}/connections/{connection_id}'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBookConnections']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBookConnections']._serialized_options = b'\x82\xd3\xe4\x93\x026\x124/api/v1/books/{book_name}/{book_version}/connections'
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBooksConnections']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['RetrieveBooksConnections']._serialized_options = b'\x82\xd3\xe4\x93\x02\x15\x12\x13/api/v1/connections'
    _globals['_LIBRARYSERVICE'].methods_by_name['UpgradeBookConnection']._options = None
    _globals['_LIBRARYSERVICE'].methods_by_name['UpgradeBookConnection']._serialized_options = b'\x82\xd3\xe4\x93\x02Q\x1aL/api/v1/books/{book_name}/{book_version}/connections/{connection_id}/upgrade:\x01*'
    _globals['_LIBRARYSERVICE']._serialized_start = 1309
    _globals['_LIBRARYSERVICE']._serialized_end = 3104