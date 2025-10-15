import argparse
import os
import sys
import textwrap
import typing
from typing import Literal, Optional, List

from openobd import ConnectionArguments, SessionArguments
from openobd.core.arguments import ExecutorArguments, ArgumentStore

COMMAND_RUN = 'run'
COMMAND_SERVE = 'serve'

'''The openOBD environment variables that can be set'''
environment_variable_spec = {
    "client_id":        "OPENOBD_PARTNER_CLIENT_ID",
    "client_secret":    "OPENOBD_PARTNER_CLIENT_SECRET",
    "cluster_id":       "OPENOBD_CLUSTER_ID",
    "grpc_host":        "OPENOBD_GRPC_HOST",
    "grpc_port":        "OPENOBD_GRPC_PORT",
    "token":            "OPENOBD_TOKEN",
    "ticket_id":        "OPENOBD_TICKET_ID",
    "connector_id":     "OPENOBD_CONNECTOR_ID",
    "log_level":        "OPENOBD_LOG_LEVEL",
}

_program = 'python -m openobd'

class EnvironmentVariableParser:
    _constructor_args: dict[str, typing.Any] = {}

    def __init__(self,
                 # openOBD gRPC server credentials
                 client_id: str = None,
                 client_secret: str = None,
                 cluster_id: str = None,
                 grpc_host: str = None,
                 grpc_port: int = None,

                 # Load the following modules with openOBD scripts
                 modules: list[str] = None,
                 unique: bool = None,
                 prefix: str = None,

                 bypass_function_broker: bool = None,
                 ticket_id: str = None,
                 connector_id: str = None,
                 token: str = None,

                 log_level: Optional[str] = None
                 ):
        """
        Initialize arguments according to the following priorities:
         - keyword argument, if not available we use:
         - command line argument, if not available we use:
         - environment variable


        :param client_id: Client id of the Jifeline Partner (Partner API credentials)
        :param client_secret: Client secret of the Jifeline Partner (Partner API credentials)
        :param cluster_id: Server cluster ('001' for Europe, '002' for USA)
        :param grpc_host: gRPC host of the openOBD service (default is 'grpc.openobd.com')
        :param grpc_port: gRPC port of the openOBD service (default is 443)
        :param modules: List of modules (paths to openOBD scripts) that need to be initialized
        :param unique: Generate a fresh openOBD script id every time we initialize the scripts (Development)
        :param prefix: Prefix the script names with a short string (max 4 characters) (Development)
        :param bypass_function_broker: Calls to other openOBD functions are not routed through the function broker when
            they are locally known.
        :param ticket_id: Create an openOBD session based on a ticket
        :param connector_id: Create an openOBD session based on a connector (Development)
        :param token: Create an openOBD session based in an authentication token
        """
        self._constructor_args["client_id"] = client_id
        self._constructor_args["client_secret"] = client_secret
        self._constructor_args["cluster_id"] = cluster_id
        self._constructor_args["host"] = grpc_host
        self._constructor_args["port"] = grpc_port

        self._constructor_args["modules"] = modules
        self._constructor_args["unique"] = unique
        self._constructor_args["prefix"] = prefix

        self._constructor_args["ticket_id"] = ticket_id
        self._constructor_args["connector_id"] = connector_id
        self._constructor_args["token"] = token
        self._constructor_args["bypass_function_broker"] = bypass_function_broker

        self._constructor_args["log_level"] = log_level

    def get_from_env_with_default(self, key: str, default: Optional[typing.Any] = None):
        if key in self._constructor_args and self._constructor_args[key] is not None:
            return self._constructor_args[key]

        if key in environment_variable_spec:
            env_key = environment_variable_spec[key]
            if env_key is not None and env_key in os.environ and os.environ[env_key] is not None:
                return os.environ[env_key]

        return default

    def parse(self) -> ArgumentStore:
        return ArgumentStore(
            session_arguments = SessionArguments(
                ticket=self.get_from_env_with_default("ticket_id"),
                token=self.get_from_env_with_default("token"),
                connector=self.get_from_env_with_default("connector_id"),
                bypass_function_broker=self.get_from_env_with_default("function", False)
            ),
            connection_arguments = ConnectionArguments(
                client_id = self.get_from_env_with_default("client_id"),
                client_secret = self.get_from_env_with_default("client_secret"),
                cluster_id = self.get_from_env_with_default("cluster_id"),
                grpc_host = self.get_from_env_with_default("grpc_host"),
                grpc_port = self.get_from_env_with_default("grpc_port")
            ),
            executor_arguments = ExecutorArguments(
                modules = self.get_from_env_with_default("modules", []),
                unique_function_ids = self.get_from_env_with_default("unique", False),
                prefix = self.get_from_env_with_default("prefix")
            ),
            log_level = self.get_from_env_with_default("log_level")
        )