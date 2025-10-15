import click

from fovus.commands.job.commands.create.job_create_command import job_create_command
from fovus.commands.job.commands.delete.job_delete_command import job_delete_command
from fovus.commands.job.commands.download.job_download_command import (
    job_download_command,
)
from fovus.commands.job.commands.generate_id.job_generate_id_command import (
    job_generate_id_command,
)
from fovus.commands.job.commands.get_default_config.job_get_default_config_command import (
    job_get_default_config_command,
)
from fovus.commands.job.commands.list_objects.job_list_objects_command import (
    job_list_objects_command,
)
from fovus.commands.job.commands.live_tail.job_live_tail_command import (
    job_live_tail_command,
)
from fovus.commands.job.commands.status.job_status_command import job_status_command
from fovus.commands.job.commands.sync_files.job_sync_command import job_sync_command
from fovus.commands.job.commands.terminate.job_terminate_command import (
    job_terminate_command,
)
from fovus.commands.job.commands.upload.job_upload_command import job_upload_command


@click.group("job")
def job_command():
    """Contains commands related to jobs."""


job_command.add_command(job_create_command)
job_command.add_command(job_delete_command)
job_command.add_command(job_download_command)
job_command.add_command(job_status_command)
job_command.add_command(job_live_tail_command)
job_command.add_command(job_sync_command)
job_command.add_command(job_terminate_command)
job_command.add_command(job_generate_id_command)
job_command.add_command(job_upload_command)
job_command.add_command(job_list_objects_command)
job_command.add_command(job_get_default_config_command)
