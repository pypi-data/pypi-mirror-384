import os
import re
from typing import Optional, Any

def redacted_str(obj: Any, redacted_attributes: list[str] = []) -> str:
    props = [prop for prop in dir(obj) if not prop.startswith('__') and not callable(getattr(obj, prop))]
    return (f"{type(obj)}(" +
            [f"{prop}={'***' if prop in redacted_attributes else getattr(obj, prop)}" for prop in props] +
            ")")

class ExecutorArguments:
    modules: list[str] = None
    unique_function_ids: bool = None
    prefix: str = None

    def __init__(self,
                 # Load the following modules with openOBD scripts
                 modules: list[str] = None,
                 unique_function_ids: bool = None,
                 prefix: str = None):
        """
        :param modules: List of modules (paths to openOBD scripts) that need to be initialized
        :param unique_function_ids: Generate a fresh openOBD script id every time we initialize the scripts (Development)
        :param prefix: Prefix the script names with a short string (max 4 characters) (Development)
        """
        self.modules = modules
        self.unique_function_ids = unique_function_ids
        self.prefix = self._filter_prefix(prefix)

    @staticmethod
    def _filter_prefix(prefix: Optional[str]):
        if prefix is None:
            return None

        '''Only alphanumeric'''
        filtered = re.sub(r'[^a-zA-Z0-9]', '', prefix)
        '''Max 4 chars'''
        return filtered[:4].upper()

    def __str__(self):
        return redacted_str(self)

class SessionArguments:
    token: Optional[str]
    ticket_id: Optional[str]
    connector_id: Optional[str]
    bypass_function_broker: bool = False

    def __init__(self,
                 # Specific 'run' arguments
                 ticket: Optional[str] = None,
                 connector: Optional[str] = None,
                 token: Optional[str] = None,
                 bypass_function_broker: bool = False):
        """
        :param ticket: Create an openOBD session based on a ticket
        :param connector: Create an openOBD session based on a connector (Development)
        :param token: Create an openOBD session based in an authentication token
        :param bypass_function_broker: Calls to other openOBD functions are not routed through the function broker when
            they are locally known.
        """
        self.ticket_id = ticket
        self.connector_id = connector
        self.token = token
        self.bypass_function_broker = bypass_function_broker

    def __str__(self):
        return redacted_str(self)

class ConnectionArguments:
    client_id: str
    client_secret: str
    cluster_id: str
    grpc_host: str
    grpc_port: int

    def __init__(self,
                 # openOBD gRPC server credentials
                 client_id: str = None,
                 client_secret: str = None,
                 cluster_id: str = None,
                 grpc_host: str = None,
                 grpc_port: int = None,
                 ):
        """
        :param client_id: Client id of the Jifeline Partner (Partner API credentials)
        :param client_secret: Client secret of the Jifeline Partner (Partner API credentials)
        :param cluster_id: Server cluster ('001' for Europe, '002' for USA)
        :param grpc_host: gRPC host of the openOBD service (default is 'grpc.openobd.com')
        :param grpc_port: gRPC port of the openOBD service (default is 443)
        """
        self.client_id = self._require_argument('client_id', client_id)
        self.client_secret = self._require_argument('client_secret', client_secret)
        self.grpc_host = grpc_host if grpc_host is not None else 'grpc.openobd.com'
        self.grpc_port = grpc_port if grpc_port is not None else 443
        self.cluster_id = self._require_argument('cluster_id', cluster_id)

    # Convenience method used to fetch arguments from environment variables
    # In older versions of the library, the environment variables were the only
    # way to provide parameters. Some places still require this setup (as a default)
    @staticmethod
    def from_environment_variables() -> "ConnectionArguments":
        return ConnectionArguments(
            client_id = os.environ.get("OPENOBD_PARTNER_CLIENT_ID"),
            client_secret = os.environ.get("OPENOBD_PARTNER_CLIENT_SECRET"),
            cluster_id = os.environ.get("OPENOBD_CLUSTER_ID"),
            grpc_host = os.environ.get("OPENOBD_GRPC_HOST"),
            grpc_port = os.environ.get("OPENOBD_GRPC_PORT"),
        )

    def _require_argument(self, argument: str, value):
        if value is None:
            message = f"Parameter '{argument}' is required but could not be found."
            raise AssertionError(message)

        return value

    def __str__(self):
        return redacted_str(self, ['client_secret'])

class ArgumentStore:
    connection_arguments: ConnectionArguments
    session_arguments: SessionArguments
    executor_arguments: ExecutorArguments

    log_level: str = 'INFO'

    def __init__(self,
                 connection_arguments: ConnectionArguments,
                 session_arguments: SessionArguments,
                 executor_arguments: ExecutorArguments,
                 log_level: str = 'INFO',
                 ):
        self.connection_arguments = connection_arguments
        self.session_arguments = session_arguments
        self.executor_arguments = executor_arguments
        self.log_level = log_level if log_level is not None else 'INFO'
