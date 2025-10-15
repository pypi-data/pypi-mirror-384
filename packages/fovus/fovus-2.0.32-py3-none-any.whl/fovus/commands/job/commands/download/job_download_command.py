import click
from typing_extensions import Tuple, Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.adapter.fovus_s3_adapter import FovusS3Adapter
from fovus.util.file_util import FileUtil
from fovus.util.util import Util


@click.command("download")
@click.argument("job_directory", type=str)
@click.option(
    "--job-id",
    type=str,
    help=(
        "The ID of the job to download files from. This is only required if JOB_DIRECTORY has not been initialized by"
        " the Fovus CLI."
    ),
)
@click.option(
    "--include-paths",
    "include_paths_tuple",
    metavar="include_paths",
    type=str,
    multiple=True,
    help=r"""
        Relative path(s) to files or folders inside the JOB_DIRECTORY to download.

        Paths support Unix shell-style wildcards, unless the --range option is used.
        When downloading a byte range, only one explicit file path may be provided,
        and wildcards are not supported.

        You can only provide either --include-paths or --exclude-paths, not both.

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

        You can only provide either --include-paths or --exclude-paths, not both.
        This option is not supported when downloading an exact byte range of a file.

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
@click.option(
    "--range",
    metavar="byte_range",
    type=str,
    help=(
        'The bytes range of the file to download. For example, --range="0-1024" downloads the first 1025 bytes'
        " (positions 0 through 1024). This option is only supported when downloading a single file."
    ),
)
def job_download_command(
    job_id: Union[str, None],
    job_directory: str,
    include_paths_tuple: Tuple[str, ...],
    exclude_paths_tuple: Tuple[str, ...],
    range: Union[str, None],
):
    """
    Download job files from Fovus Storage.

    Only new or updated files will be downloaded. If the job is running,
    the files will be synced to Fovus Storage before being downloaded.

    JOB_DIRECTORY is the directory where the files will be downloaded.
    """
    job_id = FileUtil.get_job_id(job_id, job_directory)

    include_paths = Util.parse_include_exclude_paths(include_paths_tuple)
    exclude_paths = Util.parse_include_exclude_paths(exclude_paths_tuple)

    if range:
        if not include_paths or len(include_paths) == 0:
            raise ValueError("When downloading a byte range, an explicit file path must be provided.")
        elif len(include_paths) > 1 or exclude_paths:
            raise ValueError("When downloading a byte range, only one file path is allowed.")

    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()
    fovus_s3_adapter = FovusS3Adapter(
        fovus_api_adapter,
        root_directory_path=job_directory,
        job_id=job_id,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )
    fovus_api_adapter.sync_job_files(job_id, include_paths, exclude_paths)
    fovus_s3_adapter.download_files(byte_range=range)
