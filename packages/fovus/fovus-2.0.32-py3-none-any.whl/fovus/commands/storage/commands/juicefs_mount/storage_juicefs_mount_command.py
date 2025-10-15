import json
import logging
import os
import shutil
import socket
import subprocess  # nosec
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import boto3
import click
from typing_extensions import Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.cli.helpers import install_juicefs_setup
from fovus.constants.cli_action_runner_constants import GENERIC_SUCCESS
from fovus.util.util import Util


@click.command("juicefs-mount")
@click.option(
    "--mount-storage-path",
    type=str,
    help="The path where Fovus Storage will be mounted. The default path is /fovus-juicefs/.",
)
def storage_juicefs_mount_command(mount_storage_path: Union[str, None]):
    r"""
    Mount juicefs filesyetem on your computer.

    Supported operating systems: Ubuntu, CentOS, and Redhat.

    Filesystem will be mounted as a network file system at /fovus-juicefs/ on Linux.

    Supported file operations: read, write, overwrite, delete
    """
    if not Util.is_unix():
        raise RuntimeError("JuiceFS filesystem is only suported on linux OS.")
    install_juicefs_setup()

    fovus_api_adapter = FovusApiAdapter()
    user_id = fovus_api_adapter.get_user_id()
    workspace_id = fovus_api_adapter.get_workspace_id()

    mount_storage_credentials_body = fovus_api_adapter.get_juicefs_mount_credentials(
        FovusApiAdapter.get_mount_storage_credentials_request(user_id, workspace_id)
    )

    db_url = _get_juicefs_database_url(mount_storage_credentials_body["credentials"], workspace_id, user_id)

    # Ensure AWS RDS CA bundle exists locally and enforce certificate verification in DB URL
    ca_path = _ensure_rds_ca_bundle()
    db_url = _append_ssl_params(db_url, ca_path)

    if not mount_storage_path:
        mount_storage_path = "/fovus-juicefs/"

    validation_result = _validate_mount_path(mount_storage_path, db_url)
    if validation_result["isValid"]:
        print("JuiceFS was already mounted.")
        print(GENERIC_SUCCESS)
        return

    print("Mounting filesystem...")
    _mount_juicefs(mount_storage_path, db_url)


def _get_juicefs_database_url(credentials: dict[str, str], workspace_id: str, user_id: str) -> str:
    ssm_client = boto3.client(
        "ssm",
        region_name="us-east-1",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    # Now you can use ssm_client normally
    param_response = ssm_client.get_parameter(Name=f"/juicefs/{workspace_id}/{user_id}", WithDecryption=True)
    value = param_response["Parameter"]["Value"]

    db_url = (json.loads(value))["databaseUrl"]
    if not db_url:
        raise RuntimeError("Failed to mount the storage. Missing databaseUrl.")

    return db_url


def _mount_juicefs(mount_storage_path: str, db_url: str):
    juicefs_bin = shutil.which("juicefs")
    if not juicefs_bin:
        raise RuntimeError("JuiceFS is not installed. Please run installation first.")

    try:
        subprocess.run(  # nosec
            [
                juicefs_bin,
                "mount",
                "--log-level=error",
                db_url,
                mount_storage_path,
                "--background",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        logging.error("JuiceFS mount error: %s", err.stderr)
        raise RuntimeError(f"Failed to mount storage at {mount_storage_path}") from err
    print(f"JuiceFS filesystem mounted at {mount_storage_path}")
    print(GENERIC_SUCCESS)


def _validate_mount_path(mount_storage_path: str, db_url: str) -> dict:
    validation_result = {"isValid": False, "message": ""}

    mount_bin = shutil.which("mount")
    if not mount_bin:
        raise RuntimeError("System 'mount' command not found.")
    try:
        mount_result = subprocess.run([mount_bin], capture_output=True, text=True, check=True)  # nosec B603
    except subprocess.CalledProcessError as err:
        logging.error("Failed to list system mounts: %s", err.stderr)
        raise RuntimeError("Failed to get system mounts") from err
    system_mounts = mount_result.stdout.split("\n")
    if len(system_mounts) == 0:
        validation_result["isValid"] = False
        validation_result["message"] = "No JuiceFS mount was found in the system"
        return validation_result

    juicefs_bin = shutil.which("juicefs")
    if not juicefs_bin:
        raise RuntimeError("JuiceFS is not installed. Please run installation first.")
    try:
        result = subprocess.run(
            [juicefs_bin, "status", db_url], capture_output=True, text=True, check=True
        )  # nosec B603
    except subprocess.CalledProcessError as err:
        logging.error("Failed to get JuiceFS mount status with error: %s", err.stderr)
        raise RuntimeError("Failed to get storage status") from err

    juicefs_status = json.loads(result.stdout)

    for mount in system_mounts:
        if not mount or not mount.startswith("JuiceFS:"):
            continue

        mount_parts = mount.split(" ")
        if len(mount_parts) < 3:
            continue
        fs_name = mount_parts[0].split(":")[1]
        mount_path = mount_parts[2]

        has_matched_fs_name = fs_name == juicefs_status.get("Setting", {}).get("Name", "")
        has_mount_session = any(
            session.get("MountPoint", "") == mount_path for session in juicefs_status.get("Sessions", [])
        )
        has_matched_mount_path = mount_path == mount_storage_path
        has_matched_hostname = any(
            session.get("HostName", "") == socket.gethostname() for session in juicefs_status.get("Sessions", [])
        )
        is_s3_mount = "s3" in juicefs_status.get("Setting", {}).get("Storage", "").lower()

        if (
            has_matched_fs_name
            and has_mount_session
            and has_matched_mount_path
            and has_matched_hostname
            and is_s3_mount
        ):
            validation_result["isValid"] = True
            validation_result["message"] = "JuiceFS was correctly mounted."
            return validation_result

    validation_result["isValid"] = False
    validation_result["message"] = "No valid JuiceFS mount was found"
    return validation_result


def _ensure_rds_ca_bundle() -> str:
    """
    Download AWS RDS CA bundle to a standard path, preferring region bundle first, then global.

    Returns the path to the stored certificate bundle.
    """
    ca_dir = os.path.expanduser("~/.fovus")
    preferred_path = os.path.join(ca_dir, "rds-ca-bundle.pem")
    urls = [
        "https://truststore.pki.rds.amazonaws.com/us-east-1/us-east-1-bundle.pem",
        "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem",
    ]

    def _download(to_path: str) -> bool:
        for url in urls:
            try:
                with urlopen(url) as resp:  # nosec - fixed trusted AWS endpoints
                    data = resp.read()
                # Ensure directory exists
                os.makedirs(os.path.dirname(to_path), exist_ok=True)
                with open(to_path, "wb") as out_file:
                    out_file.write(data)
                return True
            except (URLError, HTTPError, OSError) as exc:
                logging.warning("Failed to download RDS CA bundle from %s: %s", url, exc)
                continue
        return False

    # If it already exists, reuse it
    if os.path.exists(preferred_path):
        return preferred_path

    # Download into ~/.fovus
    if _download(preferred_path):
        return preferred_path

    raise RuntimeError("Failed to download AWS RDS CA bundle for JuiceFS mount.")


def _append_ssl_params(db_url: str, ca_path: str) -> str:
    """
    Append ssl verification parameters to the DB URL.

    If the URL already has query parameters, append with & otherwise with ?
    """
    if "?" in db_url:
        return f"{db_url}&sslmode=verify-full&sslrootcert={ca_path}"
    return f"{db_url}?sslmode=verify-full&sslrootcert={ca_path}"
