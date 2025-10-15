import json

import click
from typing_extensions import Tuple, Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.adapter.fovus_s3_adapter import FovusS3Adapter
from fovus.util.file_util import FileUtil
from fovus.util.util import Util


@click.command("get-default-config")
@click.option(
    "--benchmarking-profile-name",
    type=str,
    help="The name of the benchmarking profile to get the default config for.",
)
def job_get_default_config_command(
    benchmarking_profile_name: str,
):
    """
    Get the default config for a benchmarking profile.
    """
    fovus_api_adapter = FovusApiAdapter()
    default_config = fovus_api_adapter.get_default_config(benchmarking_profile_name)
    print(json.dumps(default_config))
