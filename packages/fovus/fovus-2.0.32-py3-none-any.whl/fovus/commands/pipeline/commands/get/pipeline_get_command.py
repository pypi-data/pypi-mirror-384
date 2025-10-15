import json

import click

from fovus.adapter.fovus_api_adapter import FovusApiAdapter


@click.command("get")
@click.option(
    "--pipeline-id",
    type=str,
    metavar="PIPELINE_ID",
    help="The ID of the pipeline to get the information for.",
    required=True,
)
def pipeline_get_command(pipeline_id: str):
    """
    Get pipeline information for a given pipeline ID.
    """
    fovus_api_adapter = FovusApiAdapter()

    response = fovus_api_adapter.get_pipeline(pipeline_id)
    print(json.dumps(response))
