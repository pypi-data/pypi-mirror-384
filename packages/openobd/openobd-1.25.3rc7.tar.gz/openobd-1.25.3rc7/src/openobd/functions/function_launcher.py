import copy
import sys
import typing

from openobd.core import GrpcFactory
from openobd.core.exceptions import OpenOBDException
from openobd.core.session import OpenOBDSession
from openobd.functions.function import OpenOBDFunction
from openobd.core.arguments import ConnectionArguments
from openobd_protocol.FunctionBroker.Messages.FunctionBroker_pb2 import FunctionUpdate, FunctionUpdateType, FunctionUpdateResponse, FunctionCall

from openobd.core.function_broker import OpenOBDFunctionBroker
from openobd.core.stream_handler import StreamHandler
from openobd.core.exceptions import OpenOBDStreamStoppedException

from openobd.functions.function_executor import FunctionExecutor

import threading
import logging

class FunctionLauncher:

    def __init__(self, function_broker: OpenOBDFunctionBroker, function_executor: FunctionExecutor, grpc_factory: typing.Optional[GrpcFactory] = None):
        """
        Handles communication with the function broker about functions that are available for execution.

        :param function_broker: Reference to a function broker instance
        :param function_executor: Functions that can be executed by the launcher
        """
        self.function_broker = function_broker
        self.function_executor = function_executor
        self.function_executor.load_modules(self.function_broker)
        self.stream_handler = None
        self.process_function_updates_thread = None
        self.grpc_factory = grpc_factory

        # List of threads with running functions, ordered by time of invocation
        self.threads = []

    def serve(self):
        """
        Starts serving functions to the function broker
        """
        function_registrations = self.function_executor.get_function_registrations()
        if len(function_registrations) == 0:
            logging.critical("No functions to serve!")
            logging.critical("A function should be defined according to the following pattern:\n" + '''
class ECUReset(OpenOBDFunction):

    version = "v0.1"
    name = "ECU Reset"
    description = "Reset ECU"

    def run(self):
        logging.info("Reset ECU")                        

            ''')
            sys.exit(1)

        '''Establish function update stream'''
        self.stream_handler = StreamHandler(self.function_broker.open_function_stream, outgoing_stream=True)

        for function_registration in function_registrations:
            self.stream_handler.send(FunctionUpdate(type=FunctionUpdateType.FUNCTION_UPDATE_TYPE_REQUEST, function_registration=function_registration))

        self.process_function_updates_thread = threading.Thread(target=self._process_function_updates,
                                                                name="Process function updates",
                                                                daemon=True)
        self.process_function_updates_thread.start()

        try:
            self.process_function_updates_thread.join()
        except KeyboardInterrupt as e:
            self._interrupt_launcher()

    def _process_function_updates(self):
        try:
            while True:
                function_update = self.stream_handler.receive()
                self._function_update(function_update)
        except OpenOBDStreamStoppedException:
            # This can happen when the function broker closes the stream due to no functions having been online for some time
            logging.warning("The stream to the function broker has been closed.")
        except OpenOBDException as e:
            logging.error(f"Stopped processing function updates due to an exception.")
            logging.error(e)
        finally:
            self.stream_handler.stop_stream()

    def _interrupt_launcher(self):
        # Loop over all active threads, starting with the one started most recently
        # This ensures that 'child' functions are always stopped before the 'parent' function
        for (function_reference, function_thread) in reversed(self.threads):
            if function_reference.__is_active__():
                logging.info(f"Stopping {function_reference}...")
                function_reference.interrupt()

        if self.stream_handler is not None:
            self.stream_handler.stop_stream()

    def _function_update(self, function_update: FunctionUpdate):
        if function_update.type == FunctionUpdateType.FUNCTION_UPDATE_TYPE_REQUEST:
            if function_update.HasField('function_call'):
                call = function_update.function_call
                logging.info(f"Received a function call for function id [{function_update.function_call.id}]")

                try:
                    # Test if function is available. Will raise if not available
                    self._available(call)

                    function_reference = self._get_function_instance(call)

                    function_thread = threading.Thread(target=self._call,
                                                     name=f"Function [{function_update.function_call.id}]",
                                                     args=[function_reference],
                                                     daemon=True)

                    self.threads.append((function_reference, function_thread))
                    function_thread.start()

                    # Immediately report back that we successfully received the function call and started the function
                    self.stream_handler.send(
                        FunctionUpdate(
                            type=FunctionUpdateType.FUNCTION_UPDATE_TYPE_RESPONSE,
                            function_call=function_update.function_call,
                            response=FunctionUpdateResponse.FUNCTION_UPDATE_SUCCESS
                        ))

                except Exception as e:
                    self.stream_handler.send(
                        FunctionUpdate(
                            type=FunctionUpdateType.FUNCTION_UPDATE_TYPE_RESPONSE,
                            function_call=function_update.function_call,
                            response=FunctionUpdateResponse.FUNCTION_UPDATE_FAILED,
                            response_description=str(e)
                        ))

            elif function_update.HasField('function_registration'):
                raise OpenOBDException("We do not expect a 'function_registration' as request from the function broker.")

            elif function_update.HasField('function_broker_token'):
                logging.info(f"Function update stream is still open")
                logging.debug(f"Received a new function broker token")

                # Acknowledge the ping/token update
                # We need to communicate to the broker every so often (before the Connection idle timeout of the Load Balancer)
                # or the stream (and all functions we host) gets closed
                response = copy.copy(function_update)
                response.type=FunctionUpdateType.FUNCTION_UPDATE_TYPE_RESPONSE
                self.stream_handler.send(response)

                logging.debug(f"Send new function broker token response")

            elif function_update.HasField('function_broker_reconnect'):
                raise OpenOBDException("Received a reconnect request from the function broker. We do not support it yet.")

            else:
                raise OpenOBDException("Unsupported request from the function broker")

        elif function_update.type == FunctionUpdateType.FUNCTION_UPDATE_TYPE_RESPONSE:
            logging.debug("Received function update response...")

            if function_update.HasField('function_registration') and function_update.HasField('response'):
                logging.debug(f"Received a function update for function id [{function_update.function_registration.details.id}]")

                if function_update.response == FunctionUpdateResponse.FUNCTION_UPDATE_SUCCESS:
                    logging.info(f"Function [{function_update.function_registration.details.id}] registration was successful")
                elif function_update.response == FunctionUpdateResponse.FUNCTION_UPDATE_UNAUTHORIZED:
                    logging.warning(f"Function [{function_update.function_registration.details.id}] signature check failed!")
                elif function_update.response == FunctionUpdateResponse.FUNCTION_UPDATE_UNAVAILABLE:
                    logging.warning(f"Function [{function_update.function_registration.details.id}] is no longer registered")
                else:
                    logging.warning(f"Function [{function_update.function_registration.details.id}] registration failed!")

                if function_update.HasField("response_description"):
                    logging.warning(function_update.response_description)

    def _get_function_instance(self, call: FunctionCall) -> typing.Optional[OpenOBDFunction]:
        """
        Returns an instance of the OpenOBDFunction class, implementing the function specified by the given function call object.
        :param call: Object identifying the function to call (id) and the session to use (session_info)
        :return: OpenOBDFunction instance
        """
        return self.function_executor.instantiate_function_from_uuid(id=call.id,
                                                                     openobd_session=OpenOBDSession(call.session_info, grpc_factory=self.grpc_factory),
                                                                     function_broker=self.function_broker)

    def _call(self, function: OpenOBDFunction):
        """
        Runs the given OpenOBDFunction on the current executor
        :param function:
        :return:
        """
        self.function_executor.run_function(function)

    def _available(self, call: FunctionCall):
        """
        Checks whether a function is available for the given function call. Raises an error if the function is not available
        :param call:
        :return: void
        """
        self.function_executor.instantiate_function_from_uuid(id=call.id,
                                                              openobd_session=OpenOBDSession(call.session_info, grpc_factory=self.grpc_factory),
                                                              function_broker=self.function_broker,
                                                              dry_run=True)




