from typing import Iterator

from openobd_protocol.Function.Messages import Function_pb2 as grpcFunction
from openobd_protocol.FunctionBroker.Messages import FunctionBroker_pb2 as grpcFunctionBroker
from openobd_protocol.Messages import Empty_pb2 as grpcEmpty
from openobd_protocol.SessionController.Messages import SessionController_pb2 as grpcSessionController

from openobd.core.arguments import ConnectionArguments
from openobd.core._token import Token
from openobd.core.grpc_factory import NetworkGrpcFactory, GrpcFactory
from openobd.core.exceptions import raises_openobd_exceptions

class OpenOBDFunctionBroker:

    def __init__(self, arguments: ConnectionArguments, grpc_factory: GrpcFactory = None):
        """
        Used for hosting and running third-party openOBD functions.
        Retrieves the Partner API credentials from the provided arguments.

        :keyword arguments: The arguments for the function broker.
        :keyword grpc_factory: An optional custom gRPC factory.
        """
        self.client_id = arguments.client_id
        self.client_secret = arguments.client_secret
        self.cluster_id = arguments.cluster_id

        grpc_factory = grpc_factory if grpc_factory else NetworkGrpcFactory(arguments.grpc_host, arguments.grpc_port)

        self.function_broker = grpc_factory.get_function_broker()
        self.function_broker_token = Token(self._request_function_broker_token, 300)

    def _metadata(self):
        metadata = [("authorization", "Bearer {}".format(self.function_broker_token.get_value()))]
        metadata = tuple(metadata)
        return metadata

    @raises_openobd_exceptions
    def _request_function_broker_token(self):
        """
        Requests a new function broker token. A valid function broker token is required to make any of the other calls
        to the function broker.
        """
        return self.function_broker.getFunctionBrokerToken(
            grpcSessionController.Authenticate(
                client_id=self.client_id,
                client_secret=self.client_secret,
                cluster_id=self.cluster_id
            )
        ).value

    @raises_openobd_exceptions
    def open_function_stream(self, function_update_messages: Iterator[grpcFunctionBroker.FunctionUpdate]) -> Iterator[grpcFunctionBroker.FunctionUpdate]:
        """
        Opens a stream in which functions can be made available for function callers, and through which function calls
        will be forwarded.

        :param function_update_messages: a FunctionUpdate message for each function that needs to be registered.
        :return: FunctionUpdate messages containing acknowledgements of registrations, pings, and function calls.
        """
        return self.function_broker.openFunctionStream(function_update_messages, metadata=self._metadata())

    @raises_openobd_exceptions
    def run_function(self, function_call: grpcFunctionBroker.FunctionCall) -> grpcFunctionBroker.FunctionUpdate:
        """
        Execute a function that has been registered by a function launcher.

        :param function_call: a FunctionCall defining which function to call, and the session to run the function in.
        :return: a FunctionUpdate object defining whether the function has been successfully launched.
        """
        return self.function_broker.runFunction(request=function_call, metadata=self._metadata())

    @raises_openobd_exceptions
    def get_function_registration(self, function_id: grpcFunction.FunctionId) -> grpcFunctionBroker.FunctionRegistration:
        """
        Retrieves information about the requested function. For instance, whether the function is online or not.

        :param function_id: the UUID of the function to request info on.
        :return: a FunctionRegistration object containing details on the requested function.
        """
        return self.function_broker.getFunctionRegistration(request=function_id, metadata=self._metadata())

    @raises_openobd_exceptions
    def generate_function_signature(self, request: grpcEmpty.EmptyMessage | None = None) -> grpcFunctionBroker.FunctionSignature:
        """
        Generates a new function ID and signature, which are used when registering an openOBD function.

        :return: a FunctionId object containing a new function ID and its corresponding signature.
        """
        if request is None:
            request = grpcEmpty.EmptyMessage()
        return self.function_broker.generateFunctionSignature(request=request, metadata=self._metadata())
