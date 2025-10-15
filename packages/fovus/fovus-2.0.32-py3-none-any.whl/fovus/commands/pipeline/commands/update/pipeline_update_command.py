import click

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.constants.cli_action_runner_constants import GENERIC_SUCCESS
from fovus.util.util import Util


@click.command("update")
@click.option("--pipeline-id", type=str, metavar="PIPELINE_ID", help="The ID of the pipeline to update.", required=True)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "COMPLETED", "FAILED"], case_sensitive=True),
    metavar="STATUS",
    help="The new pipeline status. Valid statuses are: RUNNING, COMPLETED, FAILED.",
    required=True,
)
def pipeline_update_command(pipeline_id: str, status: str):
    """
    Update pipeline status.
    """
    fovus_api_adapter = FovusApiAdapter()

    response = fovus_api_adapter.update_pipeline(pipeline_id, {"status": status})
    Util.print_success_message(GENERIC_SUCCESS)
    print(response)
