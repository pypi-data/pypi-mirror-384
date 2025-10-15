from typing import Union

from google.protobuf.message import Message
from openobd_protocol.Function.Messages.Function_pb2 import VariableList, ContextType

from openobd.core.exceptions import OpenOBDException
from openobd.functions.message import pack, unpack_variable_list, unpack_variable
from openobd.core.session import OpenOBDSession
from collections.abc import MutableMapping

class ContextVariables(MutableMapping):

    openobd_session = None
    context_type = None
    message_classes = None

    def __init__(self, openobd_session: OpenOBDSession,
                 context_type: ContextType = ContextType.FUNCTION_CONTEXT, message_classes = None):

        self.openobd_session = openobd_session
        self.context_type = context_type
        self.message_classes = message_classes if message_classes is not None else []

    def __getitem__(self, key: str) -> Union[str, Message, None]:
        try:
            variable = self.openobd_session.get_context_variable(key=key, context_type=self.context_type)
        except OpenOBDException as e:
            '''gRPC standard defines status code 5 as NOT_FOUND'''
            '''If the key does not exist, just return None'''
            if e.status == 5:
                return None

            '''Otherwise raise the exception'''
            raise e

        return unpack_variable(variable, self.message_classes)

    def __setitem__(self, key: str, value: Union[str, Message]):
        self.openobd_session.set_context_variable(key=key, value=pack(value),
                                                  context_type=self.context_type)

    def __delitem__(self, key: str):
        self.openobd_session.delete_context_variable(key=key,
                                                     context_type=self.context_type)

    def get_variables(self, prefix=""):
        variable_list = (self.openobd_session
                         .get_context_variable_list(prefix=prefix, context_type=self.context_type)) # type: VariableList

        return unpack_variable_list(variable_list, self.message_classes)

    def __iter__(self, prefix=""):
        return iter(self.get_variables(prefix))

    def __len__(self, prefix=""):
        return len(self.get_variables(prefix))

    def __str__(self):
        return str(self.get_variables())
