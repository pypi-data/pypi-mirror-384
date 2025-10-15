from openobd.core.grpc_factory import NetworkGrpcFactory
from openobd.core.function_broker import OpenOBDFunctionBroker
from openobd.core.session import OpenOBDSession
from openobd.core.arguments import ConnectionArguments
from openobd_protocol.FunctionBroker import FunctionBrokerServices_pb2_grpc as grpcFunctionBrokerServices
from openobd_protocol.FunctionBroker.Messages.FunctionBroker_pb2 import FunctionUpdate, FunctionUpdateResponse, \
    FunctionCall, FunctionUpdateType, FunctionBrokerToken, FunctionSignature

from openobd.functions.function_executor import FunctionExecutor
import uuid



class BypassFunctionBrokerServicer(grpcFunctionBrokerServices.functionBrokerServicer):

    def __init__(self, arguments: ConnectionArguments, executor: FunctionExecutor, grpc_factory = None):
        self.arguments = arguments
        self.executor = executor
        self.grpc_factory = grpc_factory

    def runFunction(self, request: FunctionCall, **kwargs):
        '''Run function using the function executor'''
        function_reference = self.executor.instantiate_function_from_uuid(request.id,
                                           OpenOBDSession(request.session_info, grpc_factory=self.grpc_factory),
                                           OpenOBDFunctionBroker(self.arguments, grpc_factory=self.grpc_factory))

        self.executor.run_function(function_reference)

        return FunctionUpdate(
            type=FunctionUpdateType.FUNCTION_UPDATE_TYPE_RESPONSE,
            function_call=request,
            response=FunctionUpdateResponse.FUNCTION_UPDATE_SUCCESS,
            response_description="Run function locally"
        )

    def getFunctionBrokerToken(self, request, **kwargs):
        return FunctionBrokerToken(value="<none>")

    def generateFunctionSignature(self, request, **kwargs):
        return FunctionSignature(id=str(uuid.uuid4()),signature="<bogus>")

class NetworkGrpcFactoryBypassingFunctionBroker(NetworkGrpcFactory):

    def __init__(self, arguments: ConnectionArguments, executor: FunctionExecutor, grpc_host = None, grpc_port = 443):
        super().__init__(grpc_host=grpc_host, grpc_port=grpc_port)
        self.arguments = arguments
        self.executor = executor

    def get_function_broker(
            self) -> grpcFunctionBrokerServices.functionBrokerStub | grpcFunctionBrokerServices.functionBrokerServicer:
        return BypassFunctionBrokerServicer(self.arguments, self.executor, self)

