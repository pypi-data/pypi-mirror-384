import shlex
from argparse import ArgumentParser, RawTextHelpFormatter

from midpoint_cli.prompt.base import PromptBase
from midpoint_cli.prompt.console import create_table, get_console, print_error, print_info, print_success

resource_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='resource',
    description='Manage resources.',
    epilog="""
Available commands:
  ls     List all server resources.
  test   Test a resource.
""",
)
resource_parser.add_argument('command', help='Resource command to execute.', nargs=1)
resource_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

# resource RUN parser

resource_test_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='resource test',
    description='Test a resource status.',
)
resource_test_parser.add_argument('resource', help='resource to be tested.', nargs='+')


class ResourceClientPrompt(PromptBase):
    def do_resource(self, inp):
        try:
            resource_args = shlex.split(inp)
            ns = resource_parser.parse_args(resource_args)

            if ns.command == ['ls']:
                resources = self.client.get_resources()
                connectors = self.client.get_connectors()

                for resource in resources:
                    connector = [c for c in connectors if c['OID'] == resource['connectorRef']][0]
                    del resource['connectorRef']
                    resource['Connector Type'] = connector['Connector type']
                    resource['Version'] = connector['Version']

                self._print_resources_table(resources)

                s = {r['Availability Status'] for r in resources if r['Availability Status']}
                self.error_code = 0 if s == {'up'} else 1
            elif ns.command == ['test']:
                run_ns = resource_test_parser.parse_args(resource_args[1:])
                resources = self.client.get_resources()

                for resource_id in run_ns.resource:
                    print_info(f'Testing resource {resource_id}...')
                    resource_obj = resources.find_object(resource_id)

                    if resource_obj is None:
                        print_error(f'Resource reference not found: {resource_id}')
                    else:
                        resource_oid = resource_obj.get_oid()
                        assert resource_oid is not None, 'Resource OID cannot be None'
                        status = self.client.test_resource(resource_oid)
                        if status == 'success':
                            print_success(f'Test status: {status}')
                        else:
                            print_error(f'Test status: {status}')
            else:
                self.error_code = 1
                self.error_message = f'Unknown command {ns.command}'

        except SystemExit:
            pass

    def help_resource(self):
        resource_parser.print_help()

    def do_resources(self, inp):
        return self.do_resource('ls')

    def help_resources(self):
        print('List all server resources. This is a shortcut for "resource ls"')

    @staticmethod
    def _print_resources_table(resources):
        """Print resources in a rich table format."""
        if not resources:
            print_info('No resources found')
            return

        console = get_console()
        table = create_table(title='Server Resources')

        # Add columns from first resource
        if len(resources) > 0:
            headers = list(resources[0].keys())
            for header in headers:
                # Apply colors based on column type
                if 'oid' in header.lower():
                    style = 'blue'
                elif 'name' in header.lower():
                    style = 'bright_cyan'
                elif 'status' in header.lower():
                    style = 'yellow'
                else:
                    style = 'white'
                table.add_column(header, style=style)

            # Add rows with conditional coloring for status
            for resource in resources:
                row_values = []
                for h in headers:
                    value = str(resource.get(h, ''))
                    # Color availability status
                    if 'status' in h.lower() and value:
                        if value.lower() == 'up':
                            value = f'[green]{value}[/green]'
                        elif value.lower() == 'down':
                            value = f'[red]{value}[/red]'
                    row_values.append(value)
                table.add_row(*row_values)

        console.print(table)
