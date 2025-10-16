import shlex
import sys
import unittest
from argparse import ArgumentParser, RawTextHelpFormatter

# Run command wrapper parser
from midpoint_cli.prompt.base import PromptBase

script_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='script',
    description='Run client Python scripts.',
    epilog="""
Available commands:
  run      Run a local client script.
""",
)
script_parser.add_argument('command', help='Task command to execute.')
script_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

# Script RUN parser

script_run_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='script run',
    description="""Run script. In the script execution environment, the following variables are defined:
 - tc       A TestCase instance that can be used to write assertions
 - client   The MidpointClient instance object
""",
)
script_run_parser.add_argument('script', help='A file name containing the script, or "-" to read script from stdin.')


class ScriptClientPrompt(PromptBase):
    def do_script(self, inp):
        try:
            script_args = shlex.split(inp)
            ns = script_parser.parse_args(script_args)

            if ns.command == 'run':
                run_ns = script_run_parser.parse_args(script_args[1:])

                if run_ns.script == '-':
                    code = sys.stdin.read()
                else:
                    with open(run_ns.script) as f:
                        code = f.read()

                exec(code, {'client': self.client, 'tc': unittest.TestCase()}, {})
            else:
                self.error_code = 1
                self.error_message = f'Unknown command {ns.command}'

        except SystemExit:
            pass

    def help_script(self):
        script_parser.print_help()
