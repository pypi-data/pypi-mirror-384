from collections.abc import Iterator

from openobd_protocol.Function.Messages import Function_pb2 as grpcFunction
from openobd_protocol.FunctionBroker.Messages import FunctionBroker_pb2 as grpcFunctionBroker
from openobd_protocol.SessionController.Messages import SessionController_pb2 as grpcSessionController

from openobd.core.arguments import ConnectionArguments
from openobd.core.exceptions import raises_openobd_exceptions
from openobd.core.session_controller import OpenOBDSessionController
from openobd.core.session import OpenOBDSession
from openobd.core.function_broker import OpenOBDFunctionBroker


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class OpenOBD(metaclass=SingletonMeta):

    def __init__(self, arguments: ConnectionArguments = None):
        """
        A singleton that allows for the starting and managing of openOBD sessions using the provided Partner API
        credentials. The credentials are retrieved from the arguments.
        """

        # For backwards compatibility, we allow instantiating this class without arguments. In that case,
        # the environment variables are used to configure the connection
        arguments = arguments if arguments else ConnectionArguments.from_environment_variables()
        self.session_controller = OpenOBDSessionController(arguments)
        self.function_broker = OpenOBDFunctionBroker(arguments)

    @raises_openobd_exceptions
    def start_session_on_ticket(self, ticket_id: str) -> OpenOBDSession:
        """
        Starts an openOBD session on the given ticket.

        :param ticket_id: the ticket number (or identifier) on which a session should be started.
        :return: an OpenOBDSession object representing the started session, which can be used to make gRPC calls.
        """
        response = self.session_controller.start_session_on_ticket(grpcSessionController.TicketId(value=ticket_id))
        return OpenOBDSession(response)

    @raises_openobd_exceptions
    def start_session_on_connector(self, connector_id: str) -> OpenOBDSession:
        """
        Starts an openOBD session on the given connector.

        :param connector_id: the UUID of the connector on which a session should be started.
        :return: an OpenOBDSession object representing the started session, which can be used to make gRPC calls.
        """
        response = self.session_controller.start_session_on_connector(grpcSessionController.ConnectorId(value=connector_id))
        return OpenOBDSession(response)

    @raises_openobd_exceptions
    def get_session(self, session_id: grpcSessionController.SessionId) -> grpcSessionController.SessionInfo:
        """
        Retrieves the requested openOBD session. Raises an OpenOBDException if the session does not exist.

        :param session_id: the identifier of the session to be retrieved.
        :return: a SessionInfo object representing the requested session.
        """
        return self.session_controller.get_session(session_id)

    @raises_openobd_exceptions
    def interrupt_session(self, session_id: grpcSessionController.SessionId) -> grpcSessionController.SessionInfo:
        """
        Forcefully closes the given openOBD session. This changes the session's state to "interrupted" and prevents
        further communication with the session.

        :param session_id: the identifier of the session to be interrupted.
        :return: a SessionInfo object representing the interrupted session.
        """
        return self.session_controller.interrupt_session(session_id)

    @raises_openobd_exceptions
    def get_session_list(self) -> grpcSessionController.SessionInfoList:
        """
        Retrieves all (recently) active openOBD sessions for this partner.

        :return: a SessionInfoList object containing an iterable of SessionInfo objects under its "sessions" attribute.
        """
        return self.session_controller.get_session_list()

    @raises_openobd_exceptions
    def open_function_stream(self, function_update_messages: Iterator[grpcFunctionBroker.FunctionUpdate]) -> Iterator[grpcFunctionBroker.FunctionUpdate]:
        """
        Opens a stream in which functions can be made available for function callers, and through which function calls
        will be forwarded.

        :param function_update_messages: a FunctionUpdate message for each function that needs to be registered.
        :return: FunctionUpdate messages containing acknowledgements of registrations, pings, and function calls.
        """
        return self.function_broker.open_function_stream(function_update_messages)

    @raises_openobd_exceptions
    def run_function(self, function_id: str, session_info: grpcSessionController.SessionInfo) -> grpcFunctionBroker.FunctionUpdate:
        """
        Execute a function that has been registered by a function launcher.

        :param function_id: the UUID of the function to call.
        :param session_info: the session to run the function in.
        :return: a FunctionUpdate object defining whether the function has been successfully launched.
        """
        return self.function_broker.run_function(grpcFunctionBroker.FunctionCall(id=function_id, session_info=session_info))

    @raises_openobd_exceptions
    def get_function_registration(self, function_id: str) -> grpcFunctionBroker.FunctionRegistration:
        """
        Retrieves information about the requested function. For instance, whether the function is online or not.

        :param function_id: the UUID of the function to request info on.
        :return: a FunctionRegistration object containing details on the requested function.
        """
        return self.function_broker.get_function_registration(grpcFunction.FunctionId(value=function_id))

    @raises_openobd_exceptions
    def generate_function_signature(self) -> grpcFunctionBroker.FunctionSignature:
        """
        Generates a new function ID and signature, which are used when registering an openOBD function.

        :return: a FunctionSignature object containing a new function ID and its corresponding signature.
        """
        return self.function_broker.generate_function_signature()


