import logging
from typing import Optional
from abc import ABC, abstractmethod

from openobd_protocol.FunctionBroker.Messages.FunctionBroker_pb2 import FunctionRegistration, FunctionRegistrationState, \
    FunctionVisibility
from openobd_protocol.Function.Messages.Function_pb2 import FunctionDetails, VariableList, ContextType
from openobd_protocol.Messages.Empty_pb2 import EmptyMessage
from openobd_protocol.Session.Messages.ServiceResult_pb2 import ServiceResult, Result

from openobd.core.exceptions import OpenOBDException
from openobd.core.session_token_handler import SessionTokenHandler
from openobd.core.session import OpenOBDSession
from openobd.core.function_broker import OpenOBDFunctionBroker
from openobd.functions.function_context_handler import FunctionContextHandler
from openobd.functions.function_context_variables import ContextVariables
from openobd.functions.message import pack, get_message_classes_from_function_signature, unpack_variable_list

'''When this key is found in the function results, it means we have a single return value (no dict)'''
FUNCTION_SINGLE_RETURN_VALUE = "<FUNCTION_SINGLE_RETURN_VALUE>"

class OpenOBDFunction(ABC):
    id = ""
    version = "<undef>"
    name = ""
    description = ""
    signature = ""
    dashboard = True

    openobd_session = None          # type: OpenOBDSession
    session_variables = None        # type: ContextVariables
    function_variables = None       # type: ContextVariables
    connection_variables = None     # type: ContextVariables
    result = None                   # type: ServiceResult
    message_classes = []
    _signature_classes = []

    def __init__(self):
        self.function_broker = None
        self.result = ServiceResult(result=[Result.RESULT_SUCCESS])
        self._context_finished_ = None
        self._function_registration = None

    '''
    Optionally you can pass a OpenOBDFunctionBroker (when non-standard configuration is needed)
    '''
    def initialize(self, openobd_session: OpenOBDSession, function_broker: Optional[OpenOBDFunctionBroker] = None):
        try:
            self.openobd_session = openobd_session
            self.function_broker = function_broker
            self._initialize_function_details()
            self._initialize_function_registration()
            self._context_finished_ = False
            self._signature_classes = get_message_classes_from_function_signature(self.run)

            '''
            When no message classes are defined (protobuf messages), we at least handle the message classes
            that appear in the function signature of the run() function
            '''
            if len(self.message_classes) == 0:
                self.message_classes = self._signature_classes

            '''Initialize variable contexts'''
            self._initialize_variable_contexts(self.message_classes)

        except OpenOBDException as e:
            logging.error(f"Failed to initialize openOBD function: {e}")
            self._function_registration = None
            self._context_finished_ = True

    def _initialize_variable_contexts(self, message_classes = None):
        self.session_variables = ContextVariables(self.openobd_session, ContextType.GLOBAL_CONTEXT, message_classes)
        self.connection_variables = ContextVariables(self.openobd_session, ContextType.CONNECTION_CONTEXT, message_classes)
        self.function_variables = ContextVariables(self.openobd_session, ContextType.FUNCTION_CONTEXT, message_classes)

    def _initialize_function_registration(self):
        if self.dashboard:
            visibility = FunctionVisibility.FUNCTION_VISIBILITY_DASHBOARD
        else:
            visibility = FunctionVisibility.FUNCTION_VISIBILITY_INTERNAL

        self._function_registration = FunctionRegistration(
            details=self._function_details,
            state=FunctionRegistrationState.FUNCTION_REGISTRATION_STATE_ONLINE,
            signature=self.signature,
            visibility=visibility
        )

    @abstractmethod
    def run(self, **kwargs) -> Optional[dict]:
        pass

    def get_function_registration(self):
        return self._function_registration

    def get_function_id(self):
        return self.id

    def _initialize_function_details(self, id=None, version=None, name=None, description=None, signature=None):
        self._function_details = None

        '''Check id presence, if not present we generate a fresh one'''
        if not id is None:
            self.id = id
        elif len(self.id) == 0:
            if self.function_broker is None:
                raise OpenOBDException("Function broker has not been initialized")

            function = self.function_broker.generate_function_signature()
            self.id = function.id
            self.signature = function.signature

        '''Check signature presence'''
        if not signature is None:
            self.signature = signature
        elif len(self.signature) == 0:
            raise OpenOBDException("A function signature is required in order to serve a function on the network!")

        '''Initialize (version, name, description) correctly'''
        if not version is None:
            self.version = version

        '''Only overwrite name with class name when no custom name is provided'''
        if not name is None:
            self.name = name
        elif len(self.name) == 0:
            self.name = self.__class__.__name__

        if not description is None:
            self.description = description

        self._function_details = FunctionDetails(id=self.id,
                                                 version=self.version, name=self.name, description=self.description)

    def __enter__(self):
        if self._context_finished_:
            ''' We cannot continue when the constructor failed '''
            raise OpenOBDException("Failed to construct openOBD session")

        self._authenticate()
        return self

    # Authenticate against the openOBD session for this function
    def _authenticate(self):
        try:
            # Start the SessionTokenHandler to ensure the openOBD session remains authenticated
            SessionTokenHandler(self.openobd_session)
        except OpenOBDException as e:
            logging.error(f'Activating openOBD session failed: {e}')
            self._context_finished_ = True
            raise

    def __is_active__(self):
        return not self._context_finished_

    def __del__(self):
        self.__exit__(None, None, None)

    def interrupt(self):
        self.__exit__(OpenOBDException(f"Interrupt"), f"Function [{self.id}] has been interrupted!", None)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.result = ServiceResult(result=[Result.RESULT_FAILURE])
            if exc_type == OpenOBDException:
                logging.error(f'Request failed: {exc_value}')
            else:
                logging.error(f"Something unexpected occurred [{exc_value}]")
                # if traceback is not None:
                #     logging.warning(traceback.format_exc())

        # Make sure we finish the context once
        if not hasattr(self, '_context_finished_'):
            # Something wrong with initialization, also no cleanup possible
            return

        if self._context_finished_:
            return

        self._context_finished_ = True
        if self.openobd_session is not None:
            # Check if result is set
            if self.result is None:
                self.result = ServiceResult(result=[Result.RESULT_FAILURE])

            self.openobd_session.finish(self.result)
            self.openobd_session = None

    def function_call(self, function: type | str, **kwargs):
        """
        Calls a function with the given arguments and waits until it is finished before returning its results.

        :param function: either a reference to the function's class or the ID of the function.
        :param kwargs: arguments to pass to the function.
        :return: any results set by the called function.
        """

        '''Determine the function ID depending on the given argument type'''
        if isinstance(function, type) and issubclass(function, OpenOBDFunction):
            function_id = function.id
            function_class = function
        elif isinstance(function, str):
            function_id = function
            function_class = None
        else:
            raise OpenOBDException(f"Function not found: {function}")

        '''Create fresh context'''
        function_context = FunctionContextHandler(self.openobd_session)

        '''Add eventual function arguments to the context'''
        self._set_function_arguments(**kwargs)

        '''Hand over the function handle to an executor (via the function broker)'''
        function_context.run_function(function_id, self.function_broker)

        '''Return eventual results'''
        return self.get_results(function_class)

    def _set_function_arguments(self, **kwargs):
        for key, value in kwargs.items():
            var = pack(value)
            logging.info(f"Setting function argument [{key}] to [{var}]")
            self.openobd_session.set_function_argument(key, var)

    '''Return the arguments as a dictionary'''
    def get_function_arguments(self) -> dict:
        function = self.openobd_session.function
        argument_list = function.getFunctionArgumentList(request=EmptyMessage(),
                                                         metadata=self.openobd_session.metadata())  # type: VariableList

        return unpack_variable_list(argument_list, self._signature_classes)

    def set_result(self, key, value):
        self.openobd_session.set_function_result(key=key, value=pack(value))

    '''Return the results as a dictionary'''
    def get_results(self, function_class=None):
        function = self.openobd_session.function
        result_list = function.getFunctionResultList(request=EmptyMessage(),
                                                     metadata=self.openobd_session.metadata())  # type: VariableList

        '''Convert to dictionary and unpack eventual signature protobuf Message classes'''
        message_classes = get_message_classes_from_function_signature(function_class.run) if function_class is not None else None
        variables = unpack_variable_list(result_list, message_classes)

        '''Check if there has been a return value at all, if not we return None'''
        if len(variables) == 0:
            return None

        '''Check if there was a single return value (the other remaining option is a dict)'''
        for key in variables.keys():
            if key == FUNCTION_SINGLE_RETURN_VALUE:
                '''We have a single result value, return immediately'''
                return variables[key]

        '''A dict was used as return value of the function, return this dict'''
        return variables
