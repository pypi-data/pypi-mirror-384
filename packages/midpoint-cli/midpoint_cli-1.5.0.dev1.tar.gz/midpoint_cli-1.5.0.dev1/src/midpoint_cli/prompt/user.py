import shlex
from argparse import ArgumentParser, RawTextHelpFormatter

from midpoint_cli.client import MidpointObjectList, MidpointServerError, MidpointUser

# User command wrapper parser
from midpoint_cli.prompt.base import PromptBase
from midpoint_cli.prompt.console import create_table, get_console, print_info

user_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='user',
    description='Manage server users.',
    epilog="""
Available commands:
  ls       List all users.
  search   Search for a user.
""",
)
user_parser.add_argument('command', help='User command to execute.')
user_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

# User search parser

user_search_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='user search',
    description='Search for users by substring.',
)
user_search_parser.add_argument('searchquery', help='A string fragment found in the user data.', nargs='+')

user_get_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='user get',
    description='Search for users by OID.',
)
user_get_parser.add_argument('oid', help='An OID or name value.')


class UserClientPrompt(PromptBase):
    def do_user(self, inp):
        try:
            user_args = shlex.split(inp)
            ns = user_parser.parse_args(user_args)

            if ns.command == 'ls':
                users = self.client.get_users()
                self.print_users(users)
            elif ns.command == 'search':
                search_ns = user_search_parser.parse_args(user_args[1:])
                users = self.client.get_users().filter(search_ns.searchquery)
                self.print_users(users)
            elif ns.command == 'get':
                get_ns = user_get_parser.parse_args(user_args[1:])
                try:
                    user = self.client.get_user(get_ns.oid)
                    self.print_user(user)
                except MidpointServerError as e:
                    self.error_code = 1
                    self.error_message = str(e)
            else:
                self.error_code = 1
                self.error_message = f'Unknown command {ns.command}'

        except SystemExit:
            pass

    @staticmethod
    def print_user(user: MidpointUser):
        """Print a single user's details in a rich table."""
        console = get_console()
        table = create_table(title='User Details')
        table.add_column('Attribute', style='cyan')
        table.add_column('Value', style='white')

        for attr in user.get_all_attributes():
            table.add_row(str(attr[0]), str(attr[1]))

        console.print(table)

    @staticmethod
    def print_users(users: MidpointObjectList):
        """Print a list of users in a rich table."""
        if not users:
            print_info('No users found')
            return

        console = get_console()
        table = create_table(title='Server Users')

        # Add columns from first user (assuming all users have same keys)
        if len(users) > 0:
            headers = list(users[0].keys())
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
            for user in users:
                table.add_row(*[str(user.get(h, '')) for h in headers])

        console.print(table)
        print_info(f'Total: {len(users)} users')

    @staticmethod
    def help_user():
        user_parser.print_help()

    def do_users(self, _inp):
        self.do_user('ls')

    @staticmethod
    def help_users():
        print('List all server users. This is a shortcut for "user ls"')
