import inspect

# from google.protobuf.internal.well_known_types import Any
from google.protobuf.message import Message
from openobd_protocol.Function.Messages.Function_pb2 import VariableList, Variable
from google.protobuf.any_pb2 import Any


def is_protobuf(value):
    return isinstance(value, Message) or (isinstance(value, type) and issubclass(value, Message))

def is_packed(value):
    return isinstance(value, Any)

def pack(value):
    if is_protobuf(value) and not is_packed(value):
        any = Any()
        any.Pack(value)
        return any
    return value

def unpack(value, message_classes = None):
    if not is_protobuf(value):
        return value
    if not is_packed(value):
        return value
    if message_classes is None:
        return value

    '''Try to find the data type'''
    for message_class in message_classes:
        '''Try to unpack with one of our known types'''
        msg_instance = message_class()
        if value.Unpack(msg_instance):
            return msg_instance

    return value

def unpack_variable(variable: Variable, message_classes = None):
    if variable.WhichOneof("Val") == "object":
        value = unpack(variable.object, message_classes)
    else:
        value = variable.value
    return value

def unpack_variable_list(variable_list: VariableList, message_classes = None):
    variables = {}
    for var in variable_list.variables:
        variables[var.key] = unpack_variable(var, message_classes)
    return variables

'''Inspect the signature of a function for protobuf Message types and return them as a list'''
def get_message_classes_from_function_signature(function):
    signature_classes = []
    sig = inspect.signature(function)
    for name, param in sig.parameters.items():
        if is_protobuf(param.annotation):
            '''If it is a protobuf message we will handle it for this function'''
            signature_classes.append(param.annotation)

    '''The return signature'''
    if is_protobuf(sig.return_annotation):
        signature_classes.append(sig.return_annotation)

    return signature_classes