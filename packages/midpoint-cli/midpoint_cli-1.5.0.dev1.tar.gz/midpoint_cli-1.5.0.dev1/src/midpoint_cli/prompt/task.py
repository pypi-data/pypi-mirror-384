import shlex
from argparse import ArgumentParser, RawTextHelpFormatter
from typing import cast

# Task command wrapper parser
from midpoint_cli.client import MidpointObjectTypes, MidpointTask, NopProgressMonitor, TaskExecutionFailure
from midpoint_cli.prompt.base import PromptBase
from midpoint_cli.prompt.console import (
    AnimatedProgressMonitor,
    DottedProgressMonitor,
    create_table,
    get_console,
    is_tty,
    print_error,
    print_info,
)

task_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='task',
    description='Manage server tasks.',
    epilog="""
Available commands:
  ls       List all server tasks.
  run      Run task(s) sequentially.
  suspend  Suspend task(s).
  resume   Resume task(s).
  wait     Wait for task completion.
""",
)
task_parser.add_argument('command', help='Task command to execute.')
task_parser.add_argument('arg', help='Optional command arguments.', nargs='*')

# Task RUN parser

task_run_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='task run',
    description='Run tasks synchronously.',
)
task_run_parser.add_argument('task', help='Task to be run. Can be an OID or a task name.', nargs='+')

# Task WAIT parser

task_wait_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='task wait',
    description='Wait for tasks to complete.',
)
task_wait_parser.add_argument('task', help='Task to wait for. Can be an OID or a task name.', nargs='*')

# Task GET parser

task_get_parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    prog='task get',
    description='Get data about a task.',
)
task_get_parser.add_argument('task', help='Task to wait for. Can be an OID or a task name.', nargs='*')


class TaskClientPrompt(PromptBase):
    def do_task(self, inp):
        try:
            task_args = shlex.split(inp)
            ns = task_parser.parse_args(task_args)

            if ns.command == 'ls':
                tasks = self.client.get_tasks()
                self._print_tasks_table(tasks)
            elif ns.command == 'get':
                tasks = self.client.get_tasks()
                get_ns = task_wait_parser.parse_args(task_args[1:])

                tasks_to_get = get_ns.task

                for task_id in tasks_to_get:
                    task_obj = tasks.find_object(task_id)
                    if task_obj is None:
                        print_error(f'Task reference not found: {task_id}')
                    else:
                        console = get_console()
                        console.print(cast(MidpointTask, task_obj).get_full_description())

            elif ns.command == 'wait':
                tasks = self.client.get_tasks()
                wait_ns = task_wait_parser.parse_args(task_args[1:])

                tasks_to_wait = wait_ns.task

                if len(tasks_to_wait) == 0:
                    tasks_to_wait = [task.get_oid() for task in tasks if task['Result Status'] == 'in_progress']

                for task_id in tasks_to_wait:
                    task_obj = tasks.find_object(task_id)
                    if task_obj is None:
                        print_error(f'Task reference not found: {task_id}')
                    else:
                        task_oid = task_obj.get_oid()
                        assert task_oid is not None, 'Task OID cannot be None'
                        print_info(f'Waiting for task {task_oid} / {task_obj.get_name()}')
                        progress_monitor = AnimatedProgressMonitor() if is_tty() else DottedProgressMonitor()
                        self.client.task_wait(task_oid, progress_monitor)

            elif ns.command in ['run', 'resume', 'suspend']:
                run_ns = task_run_parser.parse_args(task_args[1:])
                tasks = self.client.get_tasks()

                for task_id in run_ns.task:
                    task_obj = tasks.find_object(task_id)

                    if task_obj is None:
                        print_error(f'Task reference not found: {task_id}')
                    else:
                        task_oid = task_obj.get_oid()
                        assert task_oid is not None, 'Task OID cannot be None'
                        if ns.command == 'run' and task_obj['Execution Status'] == 'suspended':
                            print_info('Task currently suspended, activating it...')
                            self.client.task_action(task_oid, 'resume', NopProgressMonitor())
                            print_info('Now running task...')

                        print_info(f'Task {task_obj.get_name()} - {ns.command}')
                        # Create progress monitor for 'run' action
                        monitor = (
                            (AnimatedProgressMonitor() if is_tty() else DottedProgressMonitor())
                            if ns.command == 'run'
                            else NopProgressMonitor()
                        )

                        try:
                            task_result = self.client.task_action(task_oid, ns.command, monitor)

                            # Always display the task result if available
                            if task_result is not None:
                                console = get_console()
                                console.print(task_result.get_full_description())
                        except TaskExecutionFailure as e:
                            # On failure, fetch and display the task result before reporting error
                            try:
                                from xml.etree import ElementTree

                                failed_task_xml = self.client.api_client.get_element(
                                    MidpointObjectTypes.TASK.value,
                                    task_oid
                                )
                                failed_task = MidpointTask(ElementTree.fromstring(failed_task_xml))
                                console = get_console()
                                console.print(failed_task.get_full_description())
                            except Exception:
                                pass  # If we can't get the task details, just continue with the error

                            self.error_code = 1
                            self.error_message = e.message
                            break

            else:
                self.error_code = 1
                self.error_message = f'Unknown command {ns.command}'

        except SystemExit:
            pass

    @staticmethod
    def help_task():
        task_parser.print_help()

    def do_tasks(self, _inp):
        self.do_task('ls')

    @staticmethod
    def help_tasks():
        print('List all server tasks. This is a shortcut for "task ls"')

    @staticmethod
    def _print_tasks_table(tasks):
        """Print tasks in a rich table format."""
        if not tasks:
            print_info('No tasks found')
            return

        console = get_console()
        table = create_table(title='Server Tasks')

        # Add columns from first task (assuming all tasks have same keys)
        if len(tasks) > 0:
            headers = list(tasks[0].keys())
            for header in headers:
                # Apply colors based on column type
                if 'status' in header.lower():
                    style = 'yellow'
                elif 'oid' in header.lower():
                    style = 'blue'
                elif 'name' in header.lower():
                    style = 'bright_cyan'
                else:
                    style = 'white'
                table.add_column(header, style=style)

            # Add rows
            for task in tasks:
                table.add_row(*[str(task.get(h, '')) for h in headers])

        console.print(table)
