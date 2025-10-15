import importlib
import os
import inspect
import logging
import typing

from openobd_protocol.FunctionBroker.Messages.FunctionBroker_pb2 import FunctionRegistration

from openobd.functions.message import is_protobuf, pack
from openobd.core.exceptions import OpenOBDException
from openobd.core.function_broker import OpenOBDFunctionBroker
from openobd.core.arguments import ExecutorArguments
from openobd.functions.composition import OpenOBDComposition
from openobd.functions.function import OpenOBDFunction, FUNCTION_SINGLE_RETURN_VALUE


class FunctionExecutor:

    def __init__(self, arguments: ExecutorArguments):
        self.arguments = arguments
        self.functions = {}

    def load_modules(self, function_broker: OpenOBDFunctionBroker):
        if self.arguments.unique_function_ids:
            logging.info("[UNIQUE] Generating fresh function id's for all loaded functions")

        modules = self.arguments.modules
        if modules is not None:
            for module in modules:
                if not os.path.isdir(module):
                    raise Exception(f"Given module directory does not exist in working path {os.getcwd()}: {module}")

                for root, dirs, files in os.walk(module):
                    for file in files:
                        if file.endswith('.py') and file != '__init__.py':
                            rel_path = os.path.relpath(os.path.join(root, file), module)
                            mod = rel_path.replace(os.sep, '.')[:-3]  # [:-3] to remove .py
                            module_name = f"{module}.{mod}"
                            try:
                                importlib.import_module(module_name)
                                self.load_function(f"{module_name}", function_broker)
                            except ModuleNotFoundError as e:
                                logging.warning(f"Failed to import {module_name}: {e}")

    def load_function(self, module: str, function_broker: OpenOBDFunctionBroker) -> typing.Type[OpenOBDFunction]:
            logging.info(f"Loading: [{module}]")
            function_reference = None
            unique_function_ids = self.arguments.unique_function_ids
            function_name_prefix = self.arguments.prefix

            try:
                mod = importlib.import_module(module)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    # Only include classes defined in this module (not imported ones)
                    if obj.__module__ == module:
                        cls = getattr(mod, name)

                        '''Check for fingerprint of openOBD function or composition'''
                        if hasattr(cls, 'id') and hasattr(cls, 'signature') and hasattr(cls, 'name'):
                            if unique_function_ids:
                                '''Ensure fresh registration'''
                                setattr(cls, 'id', '')
                                setattr(cls, 'signature', '')

                            '''Prefix adjustment is only possible when we know that it is really a function or composition'''
                            if unique_function_ids and function_name_prefix:
                                setattr(cls, 'name', f"[{function_name_prefix}] {getattr(cls, 'name')}")

                            # Initialize the function class (Either a function or a composition)
                            try:
                                function = cls()
                                function.initialize(openobd_session=None, function_broker=function_broker)
                            except TypeError as e:
                                logging.debug(f"Not a function or composition class: {name}")
                                continue

                            if isinstance(function, OpenOBDComposition) or isinstance(function, OpenOBDFunction):
                                logging.info(f"Initializing function: [{function.id}] {function.name}")

                                '''Initialize the class in memory with the registered values'''
                                setattr(cls, 'id', function.id)
                                setattr(cls, 'signature', function.signature)
                            else:
                                '''Other classes might be helper classes, we do not need to initialize them'''
                                continue

                            function_registration = function.get_function_registration()  # type: FunctionRegistration
                            function_id = function_registration.details.id
                            if function_id in self.functions and self.functions[function_id][1] != module:
                                logging.warning(f"Function ID [{function_id}] is already used by another function")
                            self.functions[function_id] = (function_registration, module, name)
                        else:
                            '''When the expected fingerprint is not present, we do not initialize'''
                            continue

                        '''
                        First function found in a file is considered the 'main' function
                        General advice is to just define one function per file (to prevent any misunderstanding)
                        '''
                        if function_reference is None:
                            function_reference = cls
            except (ModuleNotFoundError, ValueError) as e:
                logging.critical(f"The module could not be found {module}: {e}")
            except Exception as e:
                logging.error(f"Problem loading functions from module {module}: {e}")
                raise e

            return function_reference

    def get_function_registrations(self):
        function_registrations = []
        for function_id in self.functions.keys():
            function_registrations.append(self.functions[function_id][0])
        return function_registrations

    def instantiate_function_from_uuid(self, id, openobd_session, function_broker=None, dry_run=False) -> typing.Optional[OpenOBDFunction]:
        if id not in self.functions:
            raise OpenOBDException(f"Function {id} unknown!")

        (function_registration, full_module_name, name) = self.functions[id]
        module = importlib.import_module(full_module_name)

        if dry_run:
            return None

        # Instantiate function class
        cls = getattr(module, name)

        logging.debug(f"Instantiate function [{id}]: {name}")
        function_instance = cls()
        function_instance.initialize(openobd_session=openobd_session, function_broker=function_broker)
        return function_instance

    @staticmethod
    def run_function(function: OpenOBDFunction, **kwargs):
        results = None
        with function as f:
            '''When kwargs are passed explicitly, use the kwargs from function call'''
            if len(kwargs) == 0:
                '''Load eventual arguments to pass to the run() function from session'''
                kwargs = f.get_function_arguments()

            '''Make the call to the run() function with eventual arguments'''
            results = f.run(**kwargs)
            '''Check if eventual results need to be set (only dict can be result)'''
            if isinstance(results, dict):
                for key in results.keys():
                    f.set_result(key, pack(results[key]))
            elif isinstance(results, str):
                f.set_result(FUNCTION_SINGLE_RETURN_VALUE, results)
            elif is_protobuf(results):
                f.set_result(FUNCTION_SINGLE_RETURN_VALUE, pack(results))
            elif results is not None:
                f.set_result(FUNCTION_SINGLE_RETURN_VALUE, str(results))

        return results

    def __str__(self):
        function_list = " Functions ".center(80, "-") + "\n"
        if len(self.functions) == 0:
            function_list += " " * 10 + "<none>\n"
        else:
            for function_id in self.functions.keys():
                function_registration = self.functions[function_id][0]
                function_list += "\n"
                function_list += f"             Id: {function_registration.details.id}\n"
                function_list += f"      Signature: {function_registration.signature}\n"
                function_list += f"           Name: {function_registration.details.name}\n"
                function_list += f"        Version: {function_registration.details.version}\n"
                function_list += f"    Description: {function_registration.details.description}\n"
            function_list += "\n"
        function_list += "-" * 80
        return function_list

