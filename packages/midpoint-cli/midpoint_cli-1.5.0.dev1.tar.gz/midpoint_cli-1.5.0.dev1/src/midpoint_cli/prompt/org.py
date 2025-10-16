import shlex
from argparse import ArgumentParser, RawTextHelpFormatter

# Org command wrapper parser
from midpoint_cli.prompt.base import PromptBase
from midpoint_cli.prompt.console import create_table, get_console, print_info

org_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='org',
    description='Manage server organizations.',
    epilog="""
Available commands:
  ls       List all organizations.
  search   Search for an organization.
""",
)
org_parser.add_argument('command', help='User command to execute.')
org_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

# User search parser

org_search = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='org search',
    description='Search for an organization.',
)
org_search.add_argument('searchquery', help='A string fragment found in the organization data.', nargs='+')


class OrgClientPrompt(PromptBase):
    def do_org(self, inp):
        try:
            org_args = shlex.split(inp)
            ns = org_parser.parse_args(org_args)

            if ns.command == 'ls':
                orgs = self.client.get_orgs()
                self._print_orgs_table(orgs)
            elif ns.command == 'search':
                search_ns = org_search.parse_args(org_args[1:])
                orgs = self.client.get_orgs().filter(search_ns.searchquery)
                self._print_orgs_table(orgs)
            else:
                self.error_code = 1
                self.error_message = f'Unknown command {ns.command}'

        except SystemExit:
            pass

    def help_org(self):
        org_parser.print_help()

    def do_orgs(self, inp):
        self.do_org('ls')

    def help_orgs(self):
        print('List all server organizations. This is a shortcut for "org ls"')

    @staticmethod
    def _print_orgs_table(orgs):
        """Print organizations in a rich table format."""
        if not orgs:
            print_info('No organizations found')
            return

        console = get_console()
        table = create_table(title='Organizations')

        # Add columns from first org
        if len(orgs) > 0:
            headers = list(orgs[0].keys())
            for header in headers:
                # Apply colors based on column type
                if 'oid' in header.lower():
                    style = 'blue'
                elif 'name' in header.lower():
                    style = 'bright_cyan'
                else:
                    style = 'white'
                table.add_column(header, style=style)

            # Add rows
            for org in orgs:
                table.add_row(*[str(org.get(h, '')) for h in headers])

        console.print(table)
