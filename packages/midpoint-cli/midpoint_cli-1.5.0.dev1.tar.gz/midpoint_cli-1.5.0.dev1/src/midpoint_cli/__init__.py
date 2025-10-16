import importlib
import importlib.metadata
import logging
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from configparser import ConfigParser

from midpoint_cli.client import MidpointClient
from midpoint_cli.prompt import MidpointClientPrompt
from midpoint_cli.prompt.configuration import compute_client_configuration
from midpoint_cli.prompt.console import ConsoleDisplay


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

    version = importlib.metadata.version('midpoint_cli')

    MIDPOINT_ENVIRONMENT_VARS = ['MIDPOINT_URL', 'MIDPOINT_USERNAME', 'MIDPOINT_PASSWORD']

    argument_parser = ArgumentParser(
        description='An interactive Midpoint command line client.',
        formatter_class=RawTextHelpFormatter,
        epilog="""
    Available commands:
      get       Get an XML definition from the server from an existing OID reference.
      put       Create/Update a server object based on an XML structure.
      delete    Delete a server object based on its type and OID.

      task      Manage server tasks.
      resource  Manage resources on the server.

      org       Manage organizations.
      user      Manage users.

    Server URL and credentials can also be stored in ~/.midpoint-cli.cfg, or read from environment variables MIDPOINT_URL,
    MIDPOINT_USERNAME and MIDPOINT_PASSWORD.

    Midpoint-cli version """
        + version
        + """, created and maintained by Yannick Kirschhoffer alcibiade@alcibiade.org
    """,
    )
    argument_parser.add_argument(
        '-v', '--version', help='Set the username to authenticate this session.', action='store_true'
    )
    argument_parser.add_argument(
        '-u', '--username', help='Set the username to authenticate this session.', default=None
    )
    argument_parser.add_argument(
        '-p', '--password', help='Set the password to authenticate this session.', default=None
    )
    argument_parser.add_argument('-U', '--url', help='Midpoint base URL', default=None)
    argument_parser.add_argument('command', help='Optional command to be executed immediately.', nargs='?')
    argument_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

    argument_namespace = argument_parser.parse_args(sys.argv[1:])

    if argument_namespace.version:
        print(f'Midpoint CLI Version {version}')
        sys.exit(0)

    config_parser = ConfigParser()
    config_parser.read(['midpoint-cli.cfg', os.path.expanduser('~/.midpoint-cli.cfg')])

    client_configuration = compute_client_configuration(
        argument_namespace, config_parser, [os.getenv(v) for v in MIDPOINT_ENVIRONMENT_VARS]
    )

    client = MidpointClient(client_configuration, observer=ConsoleDisplay())
    prompt = MidpointClientPrompt(client)

    if argument_namespace.command is not None:
        prompt.onecmd(argument_namespace.command + ' ' + ' '.join(argument_namespace.arg))
        sys.exit(prompt.error_code)
    else:
        prompt.cmdloop()


if __name__ == '__main__':
    main()
