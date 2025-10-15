import argparse
import os
import sys
import textwrap
from typing import Literal, Optional, List

from openobd import ConnectionArguments, SessionArguments
from openobd.core.arguments import ExecutorArguments, ArgumentStore
from openobd.environment_variables import environment_variable_spec

COMMAND_RUN = 'run'
COMMAND_SERVE = 'serve'

_program = 'python -m openobd'

class CliArgumentStore(ArgumentStore):
    file: str

    command: Literal['run', 'serve']

    def __init__(self,
                 command: Literal['run', 'serve'],

                 connection_arguments: ConnectionArguments,
                 session_arguments: SessionArguments,
                 executor_arguments: ExecutorArguments,

                 file: str,
                 log_level: str = 'INFO'):
        super().__init__(connection_arguments, session_arguments, executor_arguments, log_level)

        self.command = command
        self.file = file

    def is_command_run(self):
        return self.command == COMMAND_RUN

    def is_command_serve(self):
        return self.command == COMMAND_SERVE

class CliParser:
    # List of values as if they were set on the command line (e.g. [ '--prefix', 'abc', '--port', 80])
    _constructor_args: List[str] = []
    _command: Literal['run', 'serve'] = 'run'

    def __init__(self,
                 command: Optional[Literal['run', 'serve']] = None,

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

                 # Specific 'run' arguments
                 file: str = None,
                 bypass_function_broker: bool = None,
                 ticket: str = None,
                 connector: str = None,
                 token: str = None,
                 ):
        """
        Initialize arguments according to the following priorities:
         - keyword argument, if not available we use:
         - command line argument, if not available we use:
         - environment variable

        :param command: Either 'run' or 'serve'.
                        'run': Runs an openOBD script
                        'serve': Serves openOBD scripts to the function broker
        :param client_id: Client id of the Jifeline Partner (Partner API credentials)
        :param client_secret: Client secret of the Jifeline Partner (Partner API credentials)
        :param cluster_id: Server cluster ('001' for Europe, '002' for USA)
        :param grpc_host: gRPC host of the openOBD service (default is 'grpc.openobd.com')
        :param grpc_port: gRPC port of the openOBD service (default is 443)
        :param modules: List of modules (paths to openOBD scripts) that need to be initialized
        :param unique: Generate a fresh openOBD script id every time we initialize the scripts (Development)
        :param prefix: Prefix the script names with a short string (max 4 characters) (Development)
        :param file: The file containing an openOBD script or composition that needs to be run
        :param bypass_function_broker: Calls to other openOBD functions are not routed through the function broker when
            they are locally known.
        :param ticket: Create an openOBD session based on a ticket
        :param connector: Create an openOBD session based on a connector (Development)
        :param token: Create an openOBD session based in an authentication token
        """
        self._command = command if command is not None else 'run'

        self._set_constructor_arg('--client-id', client_id)
        self._set_constructor_arg('--client-secret', client_secret)
        self._set_constructor_arg('--cluster-id', cluster_id)
        self._set_constructor_arg('--host', grpc_host)
        self._set_constructor_arg('--port', grpc_port)

        self._set_constructor_arg('--modules', modules)
        self._set_constructor_arg('--unique', unique)
        self._set_constructor_arg('--prefix', prefix)

        self._set_constructor_arg('--file', file)
        self._set_constructor_arg('--ticket', ticket)
        self._set_constructor_arg('--connector', connector)
        self._set_constructor_arg('--token', token)
        self._set_constructor_arg('--bypass-function-broker', bypass_function_broker)

    # def _set_file(self, file_path: str = None):
    #     if file_path is None:
    #         script_path = os.path.abspath(sys.argv[0])
    #         cwd = os.getcwd()
    #         file_path = os.path.relpath(script_path, cwd)

    '''Set values when defined in constructor'''
    def _set_constructor_arg(self, argument, value):
        if value is None:
            return

        self._constructor_args.append(argument)

        '''When the argument is a flag on the commandline we are done, just return'''
        if isinstance(value, bool):
            return

        '''When the argument is a list of values'''
        if isinstance(value, list):
            for val in value:
                self._constructor_args.append(val)
            return

        self._constructor_args.append(value)

    def parse(self) -> CliArgumentStore:
        # Build a parser with the value of the environment variables as the default
        parser = ArgumentParserFactory().build()

        # The command is supposed to be the first argument. If it is not given, use the default
        if len(sys.argv) == 1:
            cli_args = [self._command]
        else:
            cli_args = sys.argv[1:]

        # Use the constructor arguments and cli arguments as default
        default_args = cli_args + self._constructor_args

        # Parse the CLI arguments
        args = parser.parse_args(default_args)

        session_arguments = None
        file = None

        if args.command == COMMAND_RUN:
            session_arguments = SessionArguments(
                ticket=args.ticket_id,
                token=args.token,
                connector=args.connector_id,
                bypass_function_broker=args.bypass_function_broker
            )
            file = args.file if 'file' in args else None

        return CliArgumentStore(
            command = args.command,
            connection_arguments = ConnectionArguments(
                client_id = args.client_id,
                client_secret = args.client_secret,
                cluster_id = args.cluster_id,
                grpc_host = args.grpc_host,
                grpc_port = args.grpc_port
            ),
            session_arguments = session_arguments,
            executor_arguments = ExecutorArguments(
                modules = args.modules,
                unique_function_ids = args.unique if 'unique' in args else False,
                prefix = args.prefix if 'prefix' in args else None
            ),
            file = file,
            log_level = args.log_level
        )

class ArgumentParserFactory:
    def build(self):
        parser = argparse.ArgumentParser(add_help=False,
                                         prog=_program,
                                         description="Run openOBD on the remote diagnostics network of Jifeline Networks",
                                         epilog=f"For detailed help for a subcommand, run \n {os.path.basename(__file__)} <command> -h")

        subparsers = parser.add_subparsers(help='Command')
        subparsers.required = False
        subparsers.dest = 'command'

        self._add_command_run(subparsers)
        self._add_command_serve(subparsers)

        return parser

    '''Run command'''
    def _add_command_run(self, subparsers):
        parser_cmd_run = subparsers.add_parser('run',
                                               help='Run a openOBD function or composition',
                                               formatter_class=argparse.RawTextHelpFormatter,
                                               )

        description = textwrap.dedent('''\
            
            [ Run options ]
            ''')

        parent_group = parser_cmd_run.add_argument_group(description=description)
        parent_group.add_argument('--file', metavar='<filename>', dest="file", help='The path to a Python file. The file should contain a class based on the OpenOBDFunction or OpenOBDComposition class.',required=True)
        self._add_modules_arguments(parent_group)
        parent_group.add_argument('--bypass-function-broker', action='store_true', dest="bypass_function_broker", help='Bypass the function broker for functions that are locally available (loaded with --modules flag).')

        description=textwrap.dedent('''\
            
            [ Session options ]
            
              An openOBD session can be instantiated by
                     <ticket id>,
                OR   <connector id> (for development),
                OR   <token>.''')

        self._add_session_argument_group(parser_cmd_run, description)

        description=textwrap.dedent('''\
            
            [ openOBD server settings ]
            
              Required when session needs to be created or subsequent function calls
              need to be made (e.g. through the function broker when hosting functions).''')
        self._add_grpc_argument_group(parser_cmd_run, description)

        self._log_level_help(parser_cmd_run)

        description = textwrap.dedent('''\
    
            -------------------------------------------------------------------------------
            
            Example:
            
                {program} run --file example_functions/test.py --modules example_functions
                
                {program} run --file example_functions/test.py --ticket 8832507 --modules example_functions --bypass-function-broker
                
            '''.format(program=_program))

        parser_cmd_run.add_argument_group(description=description)


    '''Serve command'''
    def _add_command_serve(self, subparsers):
        '''Serve'''
        parser_cmd_serve = subparsers.add_parser('serve',
                                                 help='Host openOBD functions or compositions on the Jifeline network.',
                                                 formatter_class=argparse.RawTextHelpFormatter
                                                 )

        self._add_modules_arguments(parser_cmd_serve, add_prefix_option=True)

        description = textwrap.dedent('''\
    
            [ openOBD server settings ]
            
              Required to authenticate to the function broker.''')
        self._add_grpc_argument_group(parser_cmd_serve, description)

        self._log_level_help(parser_cmd_serve)

        description = textwrap.dedent('''\
    
            -------------------------------------------------------------------------------
    
            Example:
            
                {program} serve --modules example_functions
            '''.format(program=_program))

        parser_cmd_serve.add_argument_group(description=description)


    def _add_grpc_argument_group(self, parser, description: str):
        group = parser.add_argument_group(description=description)
        group.add_argument('--host', metavar='<grpc_host>', type=str,
                           dest="grpc_host",
                           default=os.environ.get(environment_variable_spec['grpc_host'], 'grpc.openobd.com'),
                           help=f"The gRPC host of the openOBD service (default is 'grpc.openobd.com'){self._env_help('grpc_host')}")

        group.add_argument('--port', metavar='<grpc_port>', type=int,
                           dest="grpc_port",
                           default=os.environ.get(environment_variable_spec['grpc_port'], "443"),
                           help=f"The gRPC port of the openOBD service (default is 443){self._env_help('grpc_port')}")

        group.add_argument('--cluster-id', metavar='<cluster_id>', type=str,
                           dest="cluster_id",
                           default=os.environ.get(environment_variable_spec['cluster_id'], "001"),
                           help=f"The cluster id of the Jifeline partner (001=EU, 002=USA, default is '001'){self._env_help('cluster_id')}")

        group.add_argument('--client-id', metavar='<client_id>', type=str,
                           dest="client_id",
                           default=os.environ.get(environment_variable_spec['client_id']),
                           help=f"The client id of the Jifeline partner.{self._env_help('client_id')}")

        group.add_argument('--client-secret', metavar='<client_secret>', type=str,
                           dest="client_secret",
                           default=os.environ.get(environment_variable_spec['client_secret']),
                           help=f"The client secret of the Jifeline partner.{self._env_help('client_secret')}")

        return parser

    def _add_session_argument_group(self, parser, description):
        group = parser.add_argument_group(description=description)
        group.add_argument('--ticket', metavar='<ticket id>', type=str,
                           dest='ticket_id',
                           default=os.environ.get(environment_variable_spec['ticket_id']),
                           help=f"Create an openOBD session on a specific ticket{self._env_help('ticket_id')}")

        group.add_argument('--connector', metavar='<connector id>', type=str,
                           dest='connector_id',
                           default=os.environ.get(environment_variable_spec['connector_id']),
                           help=f"Create an openOBD session using a specific connector (only for development){self._env_help('connector_id')}")

        group.add_argument('--token', metavar='<token>', type=str,
                           dest='token',
                           default=os.environ.get(environment_variable_spec['token']),
                           help=f"Authentication token of an available openOBD session{self._env_help('token')}")

        return parser

    def _add_modules_arguments(self, parser, add_prefix_option=False):
        parser.add_argument('--modules', dest="modules", nargs='+', metavar='<module>', default=None, help="Path to modules containing openOBD scripts (multiple paths can be provided)", required=False)
        parser.add_argument('--unique', action='store_true', dest="unique",
                            help='Generate fresh function ids for all functions that are loaded. Guarantees unique function registrations at the function broker.')
        if not add_prefix_option:
            return

        parser.add_argument('--prefix', metavar='<prefix>', dest="prefix", default=None, help='Prepend the name of every function with this prefix (max 4 alphanumeric characters and only in combination with --unique).',required=False)


    def _log_level_help(self, parser):
        log_help_group = parser.add_argument_group(description='[ Set log level ]')

        log_help = textwrap.dedent('''\
            Possible log levels:
             [CRITICAL, ERROR, WARNING, INFO, DEBUG] (Default is 'INFO')''')

        log_help_group.add_argument('--log-level', metavar='<log level>', type=str,
                                    dest='log_level',
                                    default=os.environ.get(environment_variable_spec['log_level']),
                                    help=f"{log_help}{self._env_help('log_level')}")

    @staticmethod
    def _env_help(arg_key: str):
        return f"\n - Environment variable: [{environment_variable_spec[arg_key]}]\n "



