"""Client and server classes corresponding to protobuf-defined services."""
import grpc
from ....bdk.v2.requests import add_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_add__book__connection__pb2
from ....bdk.v2.requests import book_connection_oauth_callback_pb2 as bdk_dot_v2_dot_requests_dot_book__connection__oauth__callback__pb2
from ....bdk.v2.requests import remove_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_remove__book__connection__pb2
from ....bdk.v2.requests import retrieve_book_connections_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__connections__pb2
from ....bdk.v2.requests import retrieve_book_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__pb2
from ....bdk.v2.requests import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2
from ....bdk.v2.requests import retrieve_books_connections_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__connections__pb2
from ....bdk.v2.requests import retrieve_books_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__books__pb2
from ....bdk.v2.requests import retrieve_tags_pb2 as bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2
from ....bdk.v2.requests import test_connection_pb2 as bdk_dot_v2_dot_requests_dot_test__connection__pb2
from ....bdk.v2.requests import update_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_update__book__connection__pb2
from ....bdk.v2.requests import upgrade_book_connection_pb2 as bdk_dot_v2_dot_requests_dot_upgrade__book__connection__pb2
from ....bdk.v2.responses import book_connection_pb2 as bdk_dot_v2_dot_responses_dot_book__connection__pb2
from ....bdk.v2.responses import remove_book_connection_pb2 as bdk_dot_v2_dot_responses_dot_remove__book__connection__pb2
from ....bdk.v2.responses import retrieve_book_connections_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__connections__pb2
from ....bdk.v2.responses import retrieve_book_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__pb2
from ....bdk.v2.responses import retrieve_book_procedures_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2
from ....bdk.v2.responses import retrieve_books_connections_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__books__connections__pb2
from ....bdk.v2.responses import retrieve_books_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__books__pb2
from ....bdk.v2.responses import retrieve_tags_pb2 as bdk_dot_v2_dot_responses_dot_retrieve__tags__pb2
from ....bdk.v2.responses import test_connection_pb2 as bdk_dot_v2_dot_responses_dot_test__connection__pb2
from ....bdk.v2.responses import upgrade_book_connection_pb2 as bdk_dot_v2_dot_responses_dot_upgrade__book__connection__pb2

class LibraryServiceStub(object):
    """
    LibraryService provides read-only operations for discovering and inspecting books
    in the BDK (Book Development Kit) ecosystem. This service is designed for
    library management and book metadata retrieval without executing book procedures.

    Use cases:
    - Browsing available books and their metadata
    - Discovering book capabilities and procedures
    - Testing book connectivity before execution
    - Retrieving book categorization tags
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RetrieveBooks = channel.unary_unary('/bdk.v2.LibraryService/RetrieveBooks', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.FromString, _registered_method=True)
        self.RetrieveBook = channel.unary_unary('/bdk.v2.LibraryService/RetrieveBook', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.FromString, _registered_method=True)
        self.RetrieveBookProcedures = channel.unary_unary('/bdk.v2.LibraryService/RetrieveBookProcedures', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.FromString, _registered_method=True)
        self.TestConnection = channel.unary_unary('/bdk.v2.LibraryService/TestConnection', request_serializer=bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.FromString, _registered_method=True)
        self.RetrieveTags = channel.unary_unary('/bdk.v2.LibraryService/RetrieveTags', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2.RetrieveTagsRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__tags__pb2.RetrieveTagsResponse.FromString, _registered_method=True)
        self.AddBookConnection = channel.unary_unary('/bdk.v2.LibraryService/AddBookConnection', request_serializer=bdk_dot_v2_dot_requests_dot_add__book__connection__pb2.AddBookConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, _registered_method=True)
        self.UpdateBookConnection = channel.unary_unary('/bdk.v2.LibraryService/UpdateBookConnection', request_serializer=bdk_dot_v2_dot_requests_dot_update__book__connection__pb2.UpdateBookConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, _registered_method=True)
        self.BookConnectionOAuthCallback = channel.unary_unary('/bdk.v2.LibraryService/BookConnectionOAuthCallback', request_serializer=bdk_dot_v2_dot_requests_dot_book__connection__oauth__callback__pb2.BookConnectionOAuthCallbackRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, _registered_method=True)
        self.RemoveBookConnection = channel.unary_unary('/bdk.v2.LibraryService/RemoveBookConnection', request_serializer=bdk_dot_v2_dot_requests_dot_remove__book__connection__pb2.RemoveBookConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_remove__book__connection__pb2.RemoveBookConnectionResponse.FromString, _registered_method=True)
        self.RetrieveBookConnections = channel.unary_unary('/bdk.v2.LibraryService/RetrieveBookConnections', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsResponse.FromString, _registered_method=True)
        self.RetrieveBooksConnections = channel.unary_unary('/bdk.v2.LibraryService/RetrieveBooksConnections', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsResponse.FromString, _registered_method=True)
        self.UpgradeBookConnection = channel.unary_unary('/bdk.v2.LibraryService/UpgradeBookConnection', request_serializer=bdk_dot_v2_dot_requests_dot_upgrade__book__connection__pb2.UpgradeBookConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_upgrade__book__connection__pb2.UpgradeBookConnectionResponse.FromString, _registered_method=True)

class LibraryServiceServicer(object):
    """
    LibraryService provides read-only operations for discovering and inspecting books
    in the BDK (Book Development Kit) ecosystem. This service is designed for
    library management and book metadata retrieval without executing book procedures.

    Use cases:
    - Browsing available books and their metadata
    - Discovering book capabilities and procedures
    - Testing book connectivity before execution
    - Retrieving book categorization tags
    """

    def RetrieveBooks(self, request, context):
        """
        Retrieves a list of all available books in the library.

        This endpoint returns metadata for all books that are currently available
        in the runtime, including their names, versions, descriptions, authentication
        requirements, and capabilities.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBook(self, request, context):
        """
        Retrieves detailed information about a specific book version.

        This endpoint provides comprehensive metadata about a particular book,
        including its description, author, icon, authentication mechanisms,
        configuration parameters, and capabilities.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBookProcedures(self, request, context):
        """
        Retrieves all available procedures for the specified book version.

        This endpoint returns a list of all procedures (functions/operations) that
        can be invoked on the specified book, along with their signatures, input/output
        parameters, and metadata such as descriptions and examples.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TestConnection(self, request, context):
        """
        Tests the connectivity and authentication for a specific book.

        This endpoint validates that the provided authentication credentials work
        correctly with the specified book. It's used to verify book connectivity
        before attempting to invoke procedures that require authentication.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveTags(self, request, context):
        """
        Retrieves all available tags from all books in the library.

        This endpoint returns a consolidated list of all tags used across all books
        in the library. Tags are used for categorizing and organizing books by
        functionality, domain, or other characteristics.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddBookConnection(self, request, context):
        """
        Adds a new instance of a book to the library.

        This endpoint adds a new instance of a book, which can be used to invoke
        procedures on the book.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateBookConnection(self, request, context):
        """
        Updates an instance of a book in the library.

        This endpoint updates an instance of a book in the library.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BookConnectionOAuthCallback(self, request, context):
        """
        Callback for OAuth authentication for a book instance.

        This OAuth provider should redirect the user to this endpoint to complete the flow.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveBookConnection(self, request, context):
        """
        Removes an instance of a book from the library.
        This endpoint removes an instance of a book from the library.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBookConnections(self, request, context):
        """
        Retrieve instances of a book version.

        This endpoint returns a list of all instances of a book version.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBooksConnections(self, request, context):
        """
        Retrieve all instances of all book versions.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpgradeBookConnection(self, request, context):
        """
        Upgrade an instance of a book to a new version.

        This endpoint upgrades an instance of a book to a new version.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_LibraryServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'RetrieveBooks': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBooks, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.SerializeToString), 'RetrieveBook': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBook, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.SerializeToString), 'RetrieveBookProcedures': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBookProcedures, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.SerializeToString), 'TestConnection': grpc.unary_unary_rpc_method_handler(servicer.TestConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.SerializeToString), 'RetrieveTags': grpc.unary_unary_rpc_method_handler(servicer.RetrieveTags, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2.RetrieveTagsRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__tags__pb2.RetrieveTagsResponse.SerializeToString), 'AddBookConnection': grpc.unary_unary_rpc_method_handler(servicer.AddBookConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_add__book__connection__pb2.AddBookConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.SerializeToString), 'UpdateBookConnection': grpc.unary_unary_rpc_method_handler(servicer.UpdateBookConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_update__book__connection__pb2.UpdateBookConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.SerializeToString), 'BookConnectionOAuthCallback': grpc.unary_unary_rpc_method_handler(servicer.BookConnectionOAuthCallback, request_deserializer=bdk_dot_v2_dot_requests_dot_book__connection__oauth__callback__pb2.BookConnectionOAuthCallbackRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.SerializeToString), 'RemoveBookConnection': grpc.unary_unary_rpc_method_handler(servicer.RemoveBookConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_remove__book__connection__pb2.RemoveBookConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_remove__book__connection__pb2.RemoveBookConnectionResponse.SerializeToString), 'RetrieveBookConnections': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBookConnections, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsResponse.SerializeToString), 'RetrieveBooksConnections': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBooksConnections, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsResponse.SerializeToString), 'UpgradeBookConnection': grpc.unary_unary_rpc_method_handler(servicer.UpgradeBookConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_upgrade__book__connection__pb2.UpgradeBookConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_upgrade__book__connection__pb2.UpgradeBookConnectionResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('bdk.v2.LibraryService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bdk.v2.LibraryService', rpc_method_handlers)

class LibraryService(object):
    """
    LibraryService provides read-only operations for discovering and inspecting books
    in the BDK (Book Development Kit) ecosystem. This service is designed for
    library management and book metadata retrieval without executing book procedures.

    Use cases:
    - Browsing available books and their metadata
    - Discovering book capabilities and procedures
    - Testing book connectivity before execution
    - Retrieving book categorization tags
    """

    @staticmethod
    def RetrieveBooks(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveBooks', bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBook(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveBook', bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBookProcedures(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveBookProcedures', bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def TestConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/TestConnection', bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveTags(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveTags', bdk_dot_v2_dot_requests_dot_retrieve__tags__pb2.RetrieveTagsRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__tags__pb2.RetrieveTagsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def AddBookConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/AddBookConnection', bdk_dot_v2_dot_requests_dot_add__book__connection__pb2.AddBookConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpdateBookConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/UpdateBookConnection', bdk_dot_v2_dot_requests_dot_update__book__connection__pb2.UpdateBookConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def BookConnectionOAuthCallback(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/BookConnectionOAuthCallback', bdk_dot_v2_dot_requests_dot_book__connection__oauth__callback__pb2.BookConnectionOAuthCallbackRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_book__connection__pb2.BookConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RemoveBookConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RemoveBookConnection', bdk_dot_v2_dot_requests_dot_remove__book__connection__pb2.RemoveBookConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_remove__book__connection__pb2.RemoveBookConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBookConnections(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveBookConnections', bdk_dot_v2_dot_requests_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__book__connections__pb2.RetrieveBookConnectionsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBooksConnections(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/RetrieveBooksConnections', bdk_dot_v2_dot_requests_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__books__connections__pb2.RetrieveBooksConnectionsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def UpgradeBookConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.LibraryService/UpgradeBookConnection', bdk_dot_v2_dot_requests_dot_upgrade__book__connection__pb2.UpgradeBookConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_upgrade__book__connection__pb2.UpgradeBookConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)