from http import HTTPStatus

from typing_extensions import Literal, Union

from fovus.constants.cli_action_runner_constants import GENERIC_SUCCESS
from fovus.exception.user_exception import UserException
from fovus.util.util import Util

NUM_DECIMAL_POINTS_FILESIZE = 4


class FovusS3AdapterUtil:
    @staticmethod
    def print_pre_operation_information(
        operation: str,
        file_count: int,
        file_size_bytes: int,
        task_count: Union[int, None] = None,
        primary_unit: Literal["B", "MB", "GB"] = "MB",
    ):
        print(f"Beginning {operation}:")

        if isinstance(task_count, int):
            print(f"\tTask count:\t{task_count}")
        print(f"\tFile count:\t{file_count}")

        if primary_unit == "GB":
            total_file_size_primary = round(
                Util.convert_bytes_to_gigabytes(file_size_bytes), NUM_DECIMAL_POINTS_FILESIZE
            )
            total_file_size_secondary = None
            secondary_unit = None
        if primary_unit == "MB":
            total_file_size_primary = round(
                Util.convert_bytes_to_megabytes(file_size_bytes), NUM_DECIMAL_POINTS_FILESIZE
            )
            total_file_size_secondary = round(
                Util.convert_bytes_to_gigabytes(file_size_bytes), NUM_DECIMAL_POINTS_FILESIZE
            )
            secondary_unit = "GB"
        else:
            total_file_size_primary = file_size_bytes
            total_file_size_secondary = round(
                Util.convert_bytes_to_megabytes(file_size_bytes), NUM_DECIMAL_POINTS_FILESIZE
            )
            secondary_unit = "MB"

        file_size_info = f"{total_file_size_primary} {primary_unit}"
        if total_file_size_secondary is not None and secondary_unit is not None:
            file_size_info += f" ({total_file_size_secondary} {secondary_unit})"
        print(f"\tFile size:\t{file_size_info}")

    @staticmethod
    def print_post_operation_success(operation, is_success):
        if is_success:
            Util.print_success_message(f"{GENERIC_SUCCESS} {operation} complete.")
        else:
            Util.print_error_message(f"Failed {operation}")

        if operation == "Download":
            print(
                "Note: The download function operates as a sync. If a local file exists with the same path relative to "
                + "the job folder as a file in the cloud, and the two files are identical, it was not re-downloaded "
            )

    @staticmethod
    def parse_file_byte_range(range: Union[str, None]) -> tuple[int, int]:
        if range is None:
            return None, None

        range_list = range.split("-")
        if len(range_list) != 2:
            raise UserException(
                HTTPStatus.BAD_REQUEST,
                FovusS3AdapterUtil.__class__.__name__,
                f"Invalid range: {range}. Expected format: start-end",
            )

        start_byte = int(range_list[0])
        end_byte = int(range_list[1])
        if start_byte < 0 or end_byte < 0:
            raise UserException(
                HTTPStatus.BAD_REQUEST,
                FovusS3AdapterUtil.__class__.__name__,
                f"Invalid range: {range}. Start byte and end byte must be non-negative",
            )

        if start_byte > end_byte:
            raise UserException(
                HTTPStatus.BAD_REQUEST,
                FovusS3AdapterUtil.__class__.__name__,
                f"Invalid range: {range}. Start byte must be less than end byte",
            )

        return int(range_list[0]), int(range_list[1])
