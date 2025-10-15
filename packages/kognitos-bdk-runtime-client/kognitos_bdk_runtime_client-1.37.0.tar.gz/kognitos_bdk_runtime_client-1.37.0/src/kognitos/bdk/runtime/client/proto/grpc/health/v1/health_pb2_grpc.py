"""Client and server classes corresponding to protobuf-defined services."""
import grpc
from ....grpc.health.v1 import health_pb2 as grpc_dot_health_dot_v1_dot_health__pb2

class HealthStub(object):
    """Health is gRPC's mechanism for checking whether a server is able to handle
    RPCs. Its semantics are documented in
    https://github.com/grpc/grpc/blob/master/doc/health-checking.md.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Check = channel.unary_unary('/grpc.health.v1.Health/Check', request_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.SerializeToString, response_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.FromString, _registered_method=True)
        self.List = channel.unary_unary('/grpc.health.v1.Health/List', request_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthListRequest.SerializeToString, response_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthListResponse.FromString, _registered_method=True)
        self.Watch = channel.unary_stream('/grpc.health.v1.Health/Watch', request_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.SerializeToString, response_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.FromString, _registered_method=True)

class HealthServicer(object):
    """Health is gRPC's mechanism for checking whether a server is able to handle
    RPCs. Its semantics are documented in
    https://github.com/grpc/grpc/blob/master/doc/health-checking.md.
    """

    def Check(self, request, context):
        """Check gets the health of the specified service. If the requested service
        is unknown, the call will fail with status NOT_FOUND. If the caller does
        not specify a service name, the server should respond with its overall
        health status.

        Clients should set a deadline when calling Check, and can declare the
        server unhealthy if they do not receive a timely response.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """List provides a non-atomic snapshot of the health of all the available
        services.

        The server may respond with a RESOURCE_EXHAUSTED error if too many services
        exist.

        Clients should set a deadline when calling List, and can declare the server
        unhealthy if they do not receive a timely response.

        Clients should keep in mind that the list of health services exposed by an
        application can change over the lifetime of the process.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Watch(self, request, context):
        """Performs a watch for the serving status of the requested service.
        The server will immediately send back a message indicating the current
        serving status.  It will then subsequently send a new message whenever
        the service's serving status changes.

        If the requested service is unknown when the call is received, the
        server will send a message setting the serving status to
        SERVICE_UNKNOWN but will *not* terminate the call.  If at some
        future point, the serving status of the service becomes known, the
        server will send a new message with the service's serving status.

        If the call terminates with status UNIMPLEMENTED, then clients
        should assume this method is not supported and should not retry the
        call.  If the call terminates with any other status (including OK),
        clients should retry the call with appropriate exponential backoff.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_HealthServicer_to_server(servicer, server):
    rpc_method_handlers = {'Check': grpc.unary_unary_rpc_method_handler(servicer.Check, request_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.FromString, response_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthListRequest.FromString, response_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthListResponse.SerializeToString), 'Watch': grpc.unary_stream_rpc_method_handler(servicer.Watch, request_deserializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.FromString, response_serializer=grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('grpc.health.v1.Health', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('grpc.health.v1.Health', rpc_method_handlers)

class Health(object):
    """Health is gRPC's mechanism for checking whether a server is able to handle
    RPCs. Its semantics are documented in
    https://github.com/grpc/grpc/blob/master/doc/health-checking.md.
    """

    @staticmethod
    def Check(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/grpc.health.v1.Health/Check', grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.SerializeToString, grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/grpc.health.v1.Health/List', grpc_dot_health_dot_v1_dot_health__pb2.HealthListRequest.SerializeToString, grpc_dot_health_dot_v1_dot_health__pb2.HealthListResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Watch(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/grpc.health.v1.Health/Watch', grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckRequest.SerializeToString, grpc_dot_health_dot_v1_dot_health__pb2.HealthCheckResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)