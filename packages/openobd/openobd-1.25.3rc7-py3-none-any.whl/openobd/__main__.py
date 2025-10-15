import logging
from openobd import FunctionExecutor, OpenOBDFunctionBroker
from openobd.cli import CliParser
from openobd.core.session_builder import SessionBuilder
from openobd.functions.function_launcher import FunctionLauncher
from openobd.log import initialize_logging

if __name__ == "__main__":

    cli = CliParser().parse()
    initialize_logging(cli.log_level)

    logging.debug(f"Using cluster {cli.connection_arguments.cluster_id} and grpc server {cli.connection_arguments.grpc_host}:{cli.connection_arguments.grpc_port}")
    executor = FunctionExecutor(cli.executor_arguments)

    if cli.is_command_run():
        SessionBuilder(cli.connection_arguments, cli.session_arguments, executor).run(file_name = cli.file)

    elif cli.is_command_serve():
        function_broker = OpenOBDFunctionBroker(cli.connection_arguments)
        FunctionLauncher(function_broker, executor).serve()
