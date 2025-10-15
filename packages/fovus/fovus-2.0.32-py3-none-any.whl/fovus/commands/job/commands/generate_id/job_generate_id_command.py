import click

from fovus.adapter.fovus_api_adapter import FovusApiAdapter


@click.command("generate-id")
def job_generate_id_command():
    """Generate a unique job ID for a new job."""
    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()
    response = fovus_api_adapter.generate_job_id()
    print(f"Generated Job ID: \n{response['jobId']}")
