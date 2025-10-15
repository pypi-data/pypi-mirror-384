import json

import click
from typing_extensions import Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.util.util import Util


@click.command("list")
@click.option("--job-id", type=str, help="The ID of the job to monitor or fetch tasks from.")
@click.option("--limit", type=int, help="Maximum number of records to retrieve in this request.")
@click.option("--next_start_key", type=str, help="The key to start from for pagination of results.")
@click.option("--task-names", type=str, help="Comma-separated list of task names to filter the results.")
@click.option("--task-ids", type=str, help="Comma-separated list of task IDs to filter the results.")
def task_list_command(job_id: Union[str, None], **list_tasks_options):
    """
    List tasks of a job.

    --job-id is required.

    This command retrieves the tasks associated with a specific job ID.
    """
    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()

    task_names = list_tasks_options.get("task_names")
    task_ids = list_tasks_options.get("task_ids")

    tasks = fovus_api_adapter.get_list_tasks(
        Util.remove_none_values_recursive(
            {
                "jobId": job_id,
                "limit": list_tasks_options.get("limit", 50),
                "nextStartKey": list_tasks_options.get("next_start_key", None),
                "workspaceId": fovus_api_adapter.workspace_id,
                "filterOptions": {
                    "taskNames": task_names.split(",") if task_names else None,
                    "taskIds": task_ids.split(",") if task_ids else None,
                },
            }
        )
    )

    print(json.dumps(tasks.get("runList", []), indent=2))
