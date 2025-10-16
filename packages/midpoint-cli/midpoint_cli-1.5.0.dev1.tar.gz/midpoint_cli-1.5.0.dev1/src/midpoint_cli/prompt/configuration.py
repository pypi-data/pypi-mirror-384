from argparse import Namespace
from configparser import ConfigParser
from typing import Optional

from midpoint_cli.client import MidpointClientConfiguration


def compute_client_configuration(
    ns: Namespace, config: ConfigParser, env: list[Optional[str]]
) -> MidpointClientConfiguration:
    # Default values

    configuration = MidpointClientConfiguration()

    # Configuration files

    if 'Midpoint' in config:
        section_mp = config['Midpoint']

        if 'url' in section_mp:
            configuration.url = section_mp['url']

        if 'username' in section_mp:
            configuration.username = section_mp['username']

        if 'password' in section_mp:
            configuration.password = section_mp['password']

    # Environmment variables

    if env[0]:
        configuration.url = env[0]
    if env[1]:
        configuration.username = env[1]
    if env[2]:
        configuration.password = env[2]

    # Command-line parameters

    if ns.url:
        configuration.url = ns.url

    if ns.username:
        configuration.username = ns.username

    if ns.password:
        configuration.password = ns.password

    return configuration
