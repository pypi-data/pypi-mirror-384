from openobd_protocol.Messages import Empty_pb2 as grpcEmpty
from openobd_protocol.SessionController.Messages import SessionController_pb2 as grpcSessionController

from openobd.core._token import Token
from openobd.core.arguments import ConnectionArguments
from openobd.core.exceptions import raises_openobd_exceptions
from openobd.core.grpc_factory import NetworkGrpcFactory

class OpenOBDSessionController:

    def __init__(self, arguments: ConnectionArguments):
        """
        Used exclusively for starting and managing openOBD sessions. Retrieves the Partner API credentials from the
        environment variables unless explicitly given as kwargs.
        """
        self.client_id = arguments.client_id
        self.client_secret = arguments.client_secret
        self.cluster_id = arguments.cluster_id

        grpc_factory = NetworkGrpcFactory(arguments.grpc_host, arguments.grpc_port)

        self.session_controller = grpc_factory.get_session_controller()
        self.session_controller_token = Token(self._request_session_controller_token, 5400)

    def _metadata(self):
        metadata = [("authorization", "Bearer {}".format(self.session_controller_token.get_value()))]
        metadata = tuple(metadata)
        return metadata

    @raises_openobd_exceptions
    def _request_session_controller_token(self):
        return self.session_controller.getSessionControllerToken(
            grpcSessionController.Authenticate(
                client_id=self.client_id,
                client_secret=self.client_secret,
                cluster_id=self.cluster_id
            )
        ).value

    @raises_openobd_exceptions
    def start_session_on_ticket(self, ticket_id: grpcSessionController.TicketId) -> grpcSessionController.SessionInfo:
        """
        Starts an openOBD session on the given ticket.

        :param ticket_id: the ticket number (or identifier) on which a session should be started.
        :return: a SessionInfo object representing the started session.
        """
        return self.session_controller.startSessionOnTicket(ticket_id, metadata=self._metadata())

    @raises_openobd_exceptions
    def start_session_on_connector(self, connector_id: grpcSessionController.ConnectorId) -> grpcSessionController.SessionInfo:
        """
        Starts an openOBD session on the given connector.

        :param connector_id: the UUID of the connector on which a session should be started.
        :return: a SessionInfo object representing the started session.
        """
        return self.session_controller.startSessionOnConnector(connector_id, metadata=self._metadata())

    @raises_openobd_exceptions
    def get_session(self, session_id: grpcSessionController.SessionId) -> grpcSessionController.SessionInfo:
        """
        Retrieves the requested openOBD session. Raises an OpenOBDException if the session does not exist.

        :param session_id: the identifier of the session to be retrieved.
        :return: a SessionInfo object representing the requested session.
        """
        return self.session_controller.getSession(session_id, metadata=self._metadata())

    @raises_openobd_exceptions
    def interrupt_session(self, session_id: grpcSessionController.SessionId) -> grpcSessionController.SessionInfo:
        """
        Forcefully closes the given openOBD session. This changes the session's state to "interrupted" and prevents
        further communication with the session.

        :param session_id: the identifier of the session to be interrupted.
        :return: a SessionInfo object representing the interrupted session.
        """
        return self.session_controller.interruptSession(session_id, metadata=self._metadata())

    @raises_openobd_exceptions
    def get_session_list(self) -> grpcSessionController.SessionInfoList:
        """
        Retrieves all (recently) active openOBD sessions for this partner.

        :return: a SessionInfoList object containing an iterable of SessionInfo objects under its "sessions" attribute.
        """
        return self.session_controller.getSessionList(request=grpcEmpty.EmptyMessage(), metadata=self._metadata())
