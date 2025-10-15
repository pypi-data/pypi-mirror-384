import logging
import os
import typing

from openobd.core.openobd import OpenOBD
from openobd.core.function_broker import OpenOBDFunctionBroker
from openobd.core.grpc_factory import GrpcFactory, NetworkGrpcFactory
from openobd.core.session import OpenOBDSession
from openobd.core.arguments import ConnectionArguments, SessionArguments, ArgumentStore
from openobd_protocol.SessionController.Messages.SessionController_pb2 import SessionInfo
from openobd.functions.composition import OpenOBDComposition
from openobd.functions.function import OpenOBDFunction
from openobd.functions.bypass_function_broker import NetworkGrpcFactoryBypassingFunctionBroker
from openobd.functions.function_executor import FunctionExecutor


class EmptyFunction(OpenOBDFunction):

    def run(self):
        pass

class EmptyComposition(OpenOBDComposition):

    def run(self):
        pass


class SessionBuilder:
    session_arguments: SessionArguments
    connection_arguments: ConnectionArguments
    openobd_session = None
    function_broker = None

    def __init__(self, connection_arguments: ConnectionArguments, session_arguments: SessionArguments, function_executor: FunctionExecutor):
        self.connection_arguments = connection_arguments
        self.session_arguments = session_arguments

        self.function_executor = function_executor
        self.function_executor.load_modules(self._get_default_broker())

    @staticmethod
    def from_arguments(argument_store: ArgumentStore) -> "SessionBuilder":
        return SessionBuilder(
            argument_store.connection_arguments,
            argument_store.session_arguments,
            FunctionExecutor(argument_store.executor_arguments)
        )

    def _create_grpc_factory(self, grpc_host, grpc_port=443) -> GrpcFactory:
        if self.session_arguments.bypass_function_broker:
            if self.function_executor is None:
                raise AssertionError("When bypassing function broker, you must specify a function executor to use")

            '''Return gRPC network factory that is bypassing the function broker calls'''
            return NetworkGrpcFactoryBypassingFunctionBroker(arguments=self.connection_arguments,
                                                             executor=self.function_executor,
                                                             grpc_host=grpc_host,
                                                             grpc_port=grpc_port)
        else:
            '''Return regular gRPC network factory'''
            return NetworkGrpcFactory(grpc_host=grpc_host, grpc_port=grpc_port)

    def _get_default_broker(self):
        return OpenOBDFunctionBroker(self.connection_arguments,
                              grpc_factory=self._create_grpc_factory(
                                  grpc_host=self.connection_arguments.grpc_host,
                                  grpc_port=self.connection_arguments.grpc_port)
                              )

    def _create_session(self) -> OpenOBDSession:
        if self.session_arguments.ticket_id is not None:
            return OpenOBD(self.connection_arguments).start_session_on_ticket(ticket_id=self.session_arguments.ticket_id)

        elif self.session_arguments.connector_id is not None:
            return OpenOBD(self.connection_arguments).start_session_on_connector(connector_id=self.session_arguments.connector_id)

        elif self.session_arguments.token is not None:
            session_info = SessionInfo("", "", "", self.connection_arguments.grpc_host, self.session_arguments.token)
            return OpenOBDSession(session_info)

        raise AssertionError("Please provide a ticket id (--ticket), connector id (--connector) or a token (--token) to initialize the session.")

    def _create(self):
        openobd_session = self._create_session()
        grpc_factory = self._create_grpc_factory(openobd_session.session_info.grpc_endpoint)
        self.openobd_session = OpenOBDSession(openobd_session.session_info, grpc_factory=grpc_factory)
        self.function_broker = OpenOBDFunctionBroker(self.connection_arguments, grpc_factory=grpc_factory)

    def function(self) -> OpenOBDFunction:
        self._create()
        function = EmptyFunction()
        function.initialize(self.openobd_session, self.function_broker)
        return function

    def composition(self) -> OpenOBDComposition:
        self._create()
        composition = EmptyComposition()
        composition.initialize(self.openobd_session, self.function_broker)
        return composition

    '''This function is only used in a local setup'''
    def run(self, function: typing.Type[OpenOBDFunction] = None, file_name: typing.Optional[str] = None, **kwargs):
        '''Check if relative script path has been set, convert to module path'''
        if function is None and file_name is not None:
            file = self._script_file_to_module_path(file_name)
            if file is not None:
                '''
                Bypass the function broker for a single run call, since the file is locally loaded.
                This broker endpoint does not depend on the session info and therefore can be created
                before the openOBD session is created. Saving time in the case a function initialization fails.
                '''
                function = self.function_executor.load_function(file, self._get_default_broker())

        if function is None:
            logging.warning("Could not load function! No file reference given.")
            return None

        '''First create the session and then run the function'''
        self._create()
        function_instance = function()
        function_instance.initialize(self.openobd_session, self.function_broker)
        results = self.function_executor.run_function(function_instance, **kwargs)
        return results

    @staticmethod
    def _script_file_to_module_path(script):
        if script is None:
            return None
        return script.replace(os.sep, '.').replace('.py', '').lstrip(".")
