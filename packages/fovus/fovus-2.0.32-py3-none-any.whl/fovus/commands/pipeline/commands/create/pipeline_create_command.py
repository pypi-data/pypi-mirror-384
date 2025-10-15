import click

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.constants.cli_action_runner_constants import GENERIC_SUCCESS
from fovus.util.util import Util


@click.command("create")
@click.option(
    "--project-name",
    type=str,
    help="The project name associated with your job. "
    + "If omitted, the default project will be used. Use 'None' to specify no project.",
)
@click.option("--name", type=str, help="The pipeline name.")
def pipeline_create_command(name: str, project_name: str | None):
    """
    Create pipeline.

    This action cannot be undone.
    """
    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()
    print("Creating pipeline...")
    response = fovus_api_adapter.create_pipeline({"name": name, "projectName": project_name if project_name else None})
    Util.print_success_message(GENERIC_SUCCESS)
    print(response)
