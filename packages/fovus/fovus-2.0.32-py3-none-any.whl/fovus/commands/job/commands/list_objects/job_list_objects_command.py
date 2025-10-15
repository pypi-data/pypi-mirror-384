import json

import click
from typing_extensions import Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.adapter.fovus_s3_adapter import FovusS3Adapter
from fovus.util.util import Util


@click.command("list-objects")
@click.argument(
    "path",
    type=str,
)
@click.option("--job-id", type=str, help="The ID of the job to monitor the file from.")
@click.option(
    "--include-paths",
    "include_paths_tuple",
    metavar="include_paths",
    type=str,
    multiple=True,
    help=r"""
        The relative paths to files or folders inside the JOB_DIRECTORY that will be downloaded. Paths are provided with support for Unix shell-style wildcards.

        You can only provide either --include-paths or --exclude-paths,  not both.

        Supported wildcards:
        \* - matches any number of characters
        ? - matches any single character

        E.g. taskName/out?/\*.txt matches any .txt file in folders taskName/out1, taskName/out2, etc.

        E.g. taskName???/folder/file.txt matches taskName001/folder/file.txt, taskName123/folder/file.txt, etc.

        To specify multiple paths, this option may be provided multiple times or deliminated by a comma (``,``). To escape a comma, use two commas (``,,``).

        E.g. --include-paths "path1" --include-paths "path2"

        E.g. --include-paths "path1,path2"
        """,
)
@click.option(
    "--exclude-paths",
    "exclude_paths_tuple",
    metavar="exclude_paths",
    type=str,
    multiple=True,
    help=r"""
        The relative paths to files or folders inside the JOB_DIRECTORY that will not be downloaded. Paths are provided with support for Unix shell-style wildcards.

        You can only provide either --include-paths or --exclude-paths,  not both.

        Supported wildcards:
        \* - matches any number of characters
        ? - matches any single character

        E.g. taskName/out?/\*.txt matches any .txt file in folders taskName/out1, taskName/out2, etc.

        E.g. taskName???/folder/file.txt matches taskName001/folder/file.txt, taskName123/folder/file.txt, etc.

        To specify multiple paths, this option may be provided multiple times or deliminated by a comma (``,``). To escape a comma, use two commas (``,,``).

        E.g. --exclude-paths "path1" --exclude-paths "path2"

        E.g. --exclude-paths "path1,path2"
        """,
)
def job_list_objects_command(
    path: str, job_id: Union[str, None], include_paths_tuple: tuple[str], exclude_paths_tuple: tuple[str]
) -> None:
    """
    List objects (files and folders) at the specified PATH in a job's directory.

    You may filter the results using --include-paths or --exclude-paths, but not both.

    PATH specifies the relative path within the job (e.g., taskName/path/to/folder).

    If --job-id is provided, objects are listed from the specified job's directory.
    """
    include_paths = Util.parse_include_exclude_paths(include_paths_tuple)
    exclude_paths = Util.parse_include_exclude_paths(exclude_paths_tuple)

    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()

    if job_id is None:
        fovus_s3_adapter = FovusS3Adapter(
            fovus_api_adapter,
            root_directory_path="",
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            fovus_path=path,
        )
        response = fovus_s3_adapter.list_objects()
        print(json.dumps(response, default=default_converter, indent=2))
    else:
        fovus_s3_adapter = FovusS3Adapter(
            fovus_api_adapter,
            root_directory_path="",
            fovus_path=path,
            job_id=job_id,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        )
        response = fovus_s3_adapter.list_objects()
        print(json.dumps(response, default=default_converter, indent=2))


def default_converter(o):
    if hasattr(o, "isoformat"):
        return o.isoformat()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
