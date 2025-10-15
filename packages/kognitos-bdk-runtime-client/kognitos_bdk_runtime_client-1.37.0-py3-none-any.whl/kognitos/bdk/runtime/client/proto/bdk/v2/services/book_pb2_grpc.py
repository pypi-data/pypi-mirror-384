"""Client and server classes corresponding to protobuf-defined services."""
import grpc
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

class BookServiceStub(object):
    """
    BookService provides full runtime operations for executing book procedures
    and managing book instances. This service extends the LibraryService capabilities
    with execution and discovery features.

    Key differences from LibraryService:
    - Supports procedure execution via InvokeProcedure
    - Provides runtime environment information
    - Supports dynamic procedure discovery
    - Handles interactive question/answer flows during execution
    - Handles asynchronous procedure execution
    - Manages discoverables (dynamic entities within books)

    Use cases:
    - Executing book procedures with input parameters
    - Discovering new procedures dynamically from external systems
    - Retrieving runtime environment details
    - Managing interactive workflows with user questions
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.EnvironmentInformation = channel.unary_unary('/bdk.v2.BookService/EnvironmentInformation', request_serializer=bdk_dot_v2_dot_requests_dot_environment__information__pb2.EnvironmentInformationRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_environment__information__pb2.EnvironmentInformationResponse.FromString, _registered_method=True)
        self.RetrieveBooks = channel.unary_unary('/bdk.v2.BookService/RetrieveBooks', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.FromString, _registered_method=True)
        self.RetrieveBook = channel.unary_unary('/bdk.v2.BookService/RetrieveBook', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.FromString, _registered_method=True)
        self.RetrieveBookProcedures = channel.unary_unary('/bdk.v2.BookService/RetrieveBookProcedures', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.FromString, _registered_method=True)
        self.TestConnection = channel.unary_unary('/bdk.v2.BookService/TestConnection', request_serializer=bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.FromString, _registered_method=True)
        self.InvokeProcedure = channel.unary_unary('/bdk.v2.BookService/InvokeProcedure', request_serializer=bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2.InvokeProcedureRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.FromString, _registered_method=True)
        self.DiscoverProcedures = channel.unary_unary('/bdk.v2.BookService/DiscoverProcedures', request_serializer=bdk_dot_v2_dot_requests_dot_discover__procedures__pb2.DiscoverProceduresRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_discover__procedures__pb2.DiscoverProceduresResponse.FromString, _registered_method=True)
        self.RetrieveDiscoverables = channel.unary_unary('/bdk.v2.BookService/RetrieveDiscoverables', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesResponse.FromString, _registered_method=True)
        self.ResolvePromise = channel.unary_unary('/bdk.v2.BookService/ResolvePromise', request_serializer=bdk_dot_v2_dot_requests_dot_resolve__promise__pb2.ResolvePromiseRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.FromString, _registered_method=True)
        self.RetrieveUserInfo = channel.unary_unary('/bdk.v2.BookService/RetrieveUserInfo', request_serializer=bdk_dot_v2_dot_requests_dot_retrieve__user__info__pb2.RetrieveUserInfoRequest.SerializeToString, response_deserializer=bdk_dot_v2_dot_responses_dot_retrieve__user__info__pb2.RetrieveUserInfoResponse.FromString, _registered_method=True)

class BookServiceServicer(object):
    """
    BookService provides full runtime operations for executing book procedures
    and managing book instances. This service extends the LibraryService capabilities
    with execution and discovery features.

    Key differences from LibraryService:
    - Supports procedure execution via InvokeProcedure
    - Provides runtime environment information
    - Supports dynamic procedure discovery
    - Handles interactive question/answer flows during execution
    - Handles asynchronous procedure execution
    - Manages discoverables (dynamic entities within books)

    Use cases:
    - Executing book procedures with input parameters
    - Discovering new procedures dynamically from external systems
    - Retrieving runtime environment details
    - Managing interactive workflows with user questions
    """

    def EnvironmentInformation(self, request, context):
        """
        Retrieves information about the runtime environment.

        This endpoint provides details about the book runtime environment,
        including runtime version, API version, BCI protocol version,
        and book discovery paths.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBooks(self, request, context):
        """
        Retrieves a list of all available books (same as LibraryService).

        This endpoint returns metadata for all books that are currently available
        in the runtime. Provided for compatibility and completeness in the
        BookService interface.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBook(self, request, context):
        """
        Retrieves detailed information about a specific book (same as LibraryService).

        This endpoint provides comprehensive metadata about a particular book.
        Provided for compatibility and completeness in the BookService interface.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveBookProcedures(self, request, context):
        """
        Retrieves all available procedures for a book (same as LibraryService).

        This endpoint returns a list of all statically defined procedures that
        can be invoked on the specified book. Does not include dynamically
        discovered procedures.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TestConnection(self, request, context):
        """
        Tests connectivity and authentication for a book (same as LibraryService).

        This endpoint validates that the provided authentication credentials work
        correctly with the specified book before procedure execution.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InvokeProcedure(self, request, context):
        """
        Invokes (executes) a specific procedure within a book.

        This is the core execution endpoint that runs book procedures with provided
        input parameters. Supports:
        - Authentication for secure procedure execution
        - Input concept values (parameters)
        - Filtering expressions for data manipulation
        - Pagination (offset/limit) for large result sets
        - File offloading to external storage
        - Interactive question/answer flows
        - Output promises for asynchronous completion

        The response can be either:
        - A successful procedure result with output concepts
        - A question that requires user input to continue execution
        - A promise that can be resolved later
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DiscoverProcedures(self, request, context):
        """
        Dynamically discovers new procedures from external systems.

        This endpoint allows books to discover and register new procedures
        at runtime by connecting to external APIs, databases, or services.
        The discovered procedures become available for invocation.

        Supports:
        - Authentication for accessing external discovery sources
        - Specification of what entities to discover
        - Dynamic procedure registration
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveDiscoverables(self, request, context):
        """
        Retrieves discoverable entities from external systems.

        This endpoint returns a list of entities (like database tables, API endpoints,
        file systems, etc.) that can be discovered and potentially converted into
        executable procedures.

        Supports:
        - Search filtering by name or other criteria
        - Pagination for large discovery results
        - Authentication for accessing external systems
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ResolvePromise(self, request, context):
        """
        Attempts to resolve a promise, invoking the proper handler

        This endpoint is used to check/resolve a BDK promise. Its a continuation
        of a procedure invocation. Supports:
        - Authentication for secure procedure execution
        - File offloading to external storage
        - Interactive question/answer flows
        - Output promises for asynchronous completion

        The response can be either:
        - A successful procedure result with output concepts
        - A question that requires user input to continue execution
        - A promise that can be resolved later
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RetrieveUserInfo(self, request, context):
        """
        Retrieves information about the user from the book's connection.

        This endpoint returns information about the user (email, username and other extra attributes) from
        a book that has already been connected.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_BookServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {'EnvironmentInformation': grpc.unary_unary_rpc_method_handler(servicer.EnvironmentInformation, request_deserializer=bdk_dot_v2_dot_requests_dot_environment__information__pb2.EnvironmentInformationRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_environment__information__pb2.EnvironmentInformationResponse.SerializeToString), 'RetrieveBooks': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBooks, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.SerializeToString), 'RetrieveBook': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBook, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.SerializeToString), 'RetrieveBookProcedures': grpc.unary_unary_rpc_method_handler(servicer.RetrieveBookProcedures, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.SerializeToString), 'TestConnection': grpc.unary_unary_rpc_method_handler(servicer.TestConnection, request_deserializer=bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.SerializeToString), 'InvokeProcedure': grpc.unary_unary_rpc_method_handler(servicer.InvokeProcedure, request_deserializer=bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2.InvokeProcedureRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.SerializeToString), 'DiscoverProcedures': grpc.unary_unary_rpc_method_handler(servicer.DiscoverProcedures, request_deserializer=bdk_dot_v2_dot_requests_dot_discover__procedures__pb2.DiscoverProceduresRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_discover__procedures__pb2.DiscoverProceduresResponse.SerializeToString), 'RetrieveDiscoverables': grpc.unary_unary_rpc_method_handler(servicer.RetrieveDiscoverables, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesResponse.SerializeToString), 'ResolvePromise': grpc.unary_unary_rpc_method_handler(servicer.ResolvePromise, request_deserializer=bdk_dot_v2_dot_requests_dot_resolve__promise__pb2.ResolvePromiseRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.SerializeToString), 'RetrieveUserInfo': grpc.unary_unary_rpc_method_handler(servicer.RetrieveUserInfo, request_deserializer=bdk_dot_v2_dot_requests_dot_retrieve__user__info__pb2.RetrieveUserInfoRequest.FromString, response_serializer=bdk_dot_v2_dot_responses_dot_retrieve__user__info__pb2.RetrieveUserInfoResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('bdk.v2.BookService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('bdk.v2.BookService', rpc_method_handlers)

class BookService(object):
    """
    BookService provides full runtime operations for executing book procedures
    and managing book instances. This service extends the LibraryService capabilities
    with execution and discovery features.

    Key differences from LibraryService:
    - Supports procedure execution via InvokeProcedure
    - Provides runtime environment information
    - Supports dynamic procedure discovery
    - Handles interactive question/answer flows during execution
    - Handles asynchronous procedure execution
    - Manages discoverables (dynamic entities within books)

    Use cases:
    - Executing book procedures with input parameters
    - Discovering new procedures dynamically from external systems
    - Retrieving runtime environment details
    - Managing interactive workflows with user questions
    """

    @staticmethod
    def EnvironmentInformation(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/EnvironmentInformation', bdk_dot_v2_dot_requests_dot_environment__information__pb2.EnvironmentInformationRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_environment__information__pb2.EnvironmentInformationResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBooks(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/RetrieveBooks', bdk_dot_v2_dot_requests_dot_retrieve__books__pb2.RetrieveBooksRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__books__pb2.RetrieveBooksResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBook(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/RetrieveBook', bdk_dot_v2_dot_requests_dot_retrieve__book__pb2.RetrieveBookRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__book__pb2.RetrieveBookResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveBookProcedures(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/RetrieveBookProcedures', bdk_dot_v2_dot_requests_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__book__procedures__pb2.RetrieveBookProceduresResponseV2.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def TestConnection(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/TestConnection', bdk_dot_v2_dot_requests_dot_test__connection__pb2.TestConnectionRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_test__connection__pb2.TestConnectionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def InvokeProcedure(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/InvokeProcedure', bdk_dot_v2_dot_requests_dot_invoke__procedure__pb2.InvokeProcedureRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DiscoverProcedures(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/DiscoverProcedures', bdk_dot_v2_dot_requests_dot_discover__procedures__pb2.DiscoverProceduresRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_discover__procedures__pb2.DiscoverProceduresResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveDiscoverables(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/RetrieveDiscoverables', bdk_dot_v2_dot_requests_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__discoverables__pb2.RetrieveDiscoverablesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ResolvePromise(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/ResolvePromise', bdk_dot_v2_dot_requests_dot_resolve__promise__pb2.ResolvePromiseRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_invoke__procedure__pb2.InvokeProcedureResponseV2.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def RetrieveUserInfo(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/bdk.v2.BookService/RetrieveUserInfo', bdk_dot_v2_dot_requests_dot_retrieve__user__info__pb2.RetrieveUserInfoRequest.SerializeToString, bdk_dot_v2_dot_responses_dot_retrieve__user__info__pb2.RetrieveUserInfoResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)