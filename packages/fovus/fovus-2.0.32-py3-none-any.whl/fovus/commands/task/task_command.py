import click

from fovus.commands.task.commands.list.task_list_command import task_list_command
from fovus.commands.task.commands.terminate.task_terminate_command import (
    task_terminate_command,
)


@click.group("task")
def task_command():
    """Contains commands related to tasks."""


task_command.add_command(task_terminate_command)
task_command.add_command(task_list_command)
