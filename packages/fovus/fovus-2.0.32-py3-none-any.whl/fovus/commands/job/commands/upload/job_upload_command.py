from typing import Union

import click
from typing_extensions import Tuple

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.adapter.fovus_s3_adapter import FovusS3Adapter, UploadType
from fovus.constants.cli_constants import JOB_ID
from fovus.util.util import Util


@click.command("upload")
@click.argument(
    "local_path",
    type=str,
)
@click.argument(
    "fovus_path",
    type=str,
    required=False,
)
@click.option(
    "--job-id",
    JOB_ID,
    type=str,
    multiple=False,
    help="The ID of the job to which files will be uploaded.",
    required=True,
)
@click.option(
    "--include-paths",
    "include_paths_tuple",
    metavar="include_paths",
    type=str,
    multiple=True,
    help=r"""
        The relative paths to files or folders inside the LOCAL_PATH that will be uploaded. Paths are provided with support for Unix shell-style wildcards.

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
        The relative paths to files or folders inside the LOCAL_PATH that will be uploaded. Paths are provided with support for Unix shell-style wildcards.

        You can only provide either --include-paths or --exclude-paths,  not both.

        Supported wildcards:
        \* - matches any number of characters
        ? - matches any single character

        E.g. out?/\*.txt matches any .txt file in folders out1, out2, etc.

        E.g. folder???/file.txt matches folder001/file.txt, folder123/file.txt, etc.

        To specify multiple paths, this option may be provided multiple times or deliminated by a comma (``,``). To escape a comma, use two commas (``,,``).

        E.g. --exclude-paths "path1" --exclude-paths "path2"

        E.g. --exclude-paths "path1,path2"
        """,
)
@click.option(
    "--empty-dir",
    "empty_dir",
    metavar="empty_dir",
    type=bool,
)
def job_upload_command(
    local_path: str,
    fovus_path: Union[str, None],
    job_id: str | None,
    include_paths_tuple: Tuple[str, ...],
    exclude_paths_tuple: Tuple[str, ...],
    empty_dir: bool = False,
):
    """
    Upload files or folders to a job in Fovus Storage.

    LOCAL_PATH: Path to the local file or directory to upload.

    FOVUS_PATH: (Optional) Relative path within the job's storage location in Fovus where files will be uploaded.

    Use --job-id to specify the target job. You may filter files to upload using --include-paths or --exclude-paths.
    """
    include_paths = Util.parse_include_exclude_paths(include_paths_tuple)
    exclude_paths = Util.parse_include_exclude_paths(exclude_paths_tuple)

    # TODO: validate job_id exists

    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()
    fovus_s3_adapter = FovusS3Adapter(
        fovus_api_adapter,
        root_directory_path=local_path,
        job_id=job_id,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        fovus_path=fovus_path if fovus_path else None,
    )

    if empty_dir:
        fovus_s3_adapter.fovus_path = None
        fovus_s3_adapter.create_s3_empty_folders_direct(local_path, upload_type=UploadType.UPLOAD)
    else:
        fovus_s3_adapter.upload_storage_files(upload_type=UploadType.UPLOAD)
