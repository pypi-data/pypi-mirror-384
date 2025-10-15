import click

from fovus.commands.pipeline.commands.create.pipeline_create_command import (
    pipeline_create_command,
)
from fovus.commands.pipeline.commands.get.pipeline_get_command import (
    pipeline_get_command,
)
from fovus.commands.pipeline.commands.update.pipeline_update_command import (
    pipeline_update_command,
)


@click.group("pipeline")
def pipeline_command():
    """Contains commands related to pipeline."""


pipeline_command.add_command(pipeline_create_command)
pipeline_command.add_command(pipeline_update_command)
pipeline_command.add_command(pipeline_get_command)
