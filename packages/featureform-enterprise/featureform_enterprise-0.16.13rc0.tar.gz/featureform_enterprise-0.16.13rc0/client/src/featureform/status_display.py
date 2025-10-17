import sys
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

from featureform.grpc_client import GrpcClient
from featureform.proto import metadata_pb2
from featureform.resources import (
    ErrorInfo,
    FeatureVariant,
    FeatureView,
    LabelVariant,
    OnDemandFeatureVariant,
    Provider,
    Resource,
    ResourceState,
    SourceVariant,
    StreamFeature,
    StreamLabel,
    TrainingSetVariant,
)
from .enums import ResourceType, ResourceStatus

# maximum number of dots printing when featureform apply for Running...
MAX_NUM_RUNNING_DOTS = 10
SECONDS_BETWEEN_STATUS_CHECKS = 2
MAX_COMPLETED_TICKS = 1
NUM_DISPLAY_ROWS = 25

READY = ResourceStatus.READY.value
CREATED = ResourceStatus.CREATED.value
PENDING = ResourceStatus.PENDING.value
NO_STATUS = ResourceStatus.NO_STATUS.value
FAILED = ResourceStatus.FAILED.value
RUNNING = ResourceStatus.RUNNING.value


def display_statuses(grpc_client: GrpcClient, resources: List[Resource], host):
    StatusDisplayer(grpc_client, resources).display(host)


@dataclass
class DisplayStatus:
    resource_type: ResourceType
    name: str
    variant: Optional[str]
    status: str = NO_STATUS
    error: str = ""
    has_health_check: bool = False
    is_deleted: bool = False  # Added for delete operations

    def __post_init__(self):
        if not self.variant:
            self.variant = None

    def is_finished(self) -> bool:
        # For delete operations
        if self.is_deleted:
            return self.status in [READY, FAILED]

        # For regular operations
        return (
            self.status == READY
            or self.status == FAILED
            or (
                self.resource_type is ResourceType.PROVIDER
                and self.status == NO_STATUS
                and not self.has_health_check
            )  # Provider is a special case
        )

    @classmethod
    def from_resource(self, resource: Resource):
        variant = getattr(resource, "variant", None)
        return DisplayStatus(
            resource_type=resource.get_resource_type(),
            name=resource.name,
            variant=variant,
            status=resource.status,
            error=resource.error,
            has_health_check=bool(getattr(resource, "has_health_check", False)),
        )

    def has_variant(self) -> bool:
        return self.variant is not None and self.variant != ""

    def display_name(self) -> str:
        return self.identifier(" ")

    def identifier(self, separator: str = ":") -> str:
        return (
            self.name
            if not self.has_variant()
            else f"{self.name}{separator}{self.variant}"
        )


class ResourceTableRow:
    def __init__(self, resource: Resource, status: DisplayStatus):
        self._status = status
        self._time_ticks = 0
        if not resource:
            raise ValueError("Resource cannot be empty")
        self.name = resource.name
        self.resource = resource

    def update_status(
        self, new_status: ResourceStatus = None, error=None, is_deleted=None
    ):
        if error is None and new_status is None and is_deleted is None:
            raise ValueError(f"No updates provided to status for {self.name}")
        if error is not None:
            self._status.error = error
        if new_status is not None:
            self._status.status = new_status
        if is_deleted is not None:
            self._status.is_deleted = is_deleted

    def get_status(self) -> DisplayStatus:
        return self._status

    # One time tick corresponds to an iteration of the "while True" loop of display()
    def update_time_tick(self):
        self._time_ticks += 1

    def get_time_ticks(self):
        return self._time_ticks

    def get_status_resourcetype(self):
        return (
            ResourceType.TRANSFORMATION
            if (
                isinstance(self.resource, SourceVariant)
                and self.resource.is_transformation_type()
            )
            else self._status.resource_type
        )

    def get_status_string(self):
        return (
            self._status.status
            if self._status.resource_type is not ResourceType.PROVIDER
            or self._status.has_health_check
            else CREATED
        )


class StatusDisplayer:
    RESOURCE_TYPES_TO_CHECK = {
        FeatureVariant,
        OnDemandFeatureVariant,
        TrainingSetVariant,
        LabelVariant,
        SourceVariant,
        StreamFeature,
        StreamLabel,
        FeatureView,
        Provider,
    }

    STATUS_TO_COLOR = {
        READY: "green",
        CREATED: "green",
        PENDING: "white",
        NO_STATUS: "white",
        FAILED: "red",
        RUNNING: "yellow",
    }

    def __init__(self, grpc_client: GrpcClient, resources: List[Resource]):
        filtered_resources = filter(
            lambda r: any(
                isinstance(r, resource_type)
                for resource_type in self.RESOURCE_TYPES_TO_CHECK
            ),
            resources,
        )
        self._grpc_client = grpc_client
        self.success_list: List[ResourceTableRow] = []
        self.failed_list: List[ResourceTableRow] = []
        self.display_table_list: List[ResourceTableRow] = []
        self.unprocessed_resources: List[ResourceTableRow] = []

        for r in filtered_resources:
            self.unprocessed_resources.append(
                ResourceTableRow(r, DisplayStatus.from_resource(r))
            )

    def simple_poll(self, task_map: Dict[Tuple[int, str, str], str]):
        """Simple polling loop for delete/prune operations using task IDs.

        Args:
            task_map: Dict mapping (name, variant, resource_type) tuples to task IDs
        """
        if not task_map:
            print("No resources to monitor")
            return

        print(f"Monitoring {len(task_map)} resource(s):")
        for (res_type, name, variant), task_id in task_map.items():
            identifier = name if not variant else f"{name}:{variant}"
            print(f"  - {identifier} (task {task_id})")
        print()

        incomplete = dict(task_map)
        while incomplete:
            task_ids = list(incomplete.values())
            try:
                resp = self._grpc_client.GetTaskStatuses(
                    metadata_pb2.GetTaskStatusesRequest(task_ids=task_ids)
                )
            except Exception as e:
                # res_key is now a tuple (name, variant, res_type)
                for res_key, task_id in incomplete.items():
                    res_type, name, variant = res_key
                    identifier = name if not variant else f"{name}:{variant}"
                    print(f"✗ {identifier} - " f"Error fetching task {task_id}: {e}")
                raise

            status_map = {ts.task_id: ts for ts in resp.task_statuses}
            still_incomplete: Dict[Tuple[str, str, int], str] = {}

            for res_key, task_id in incomplete.items():
                name, variant, res_type = res_key
                task_status = status_map.get(task_id)

                if not task_status:
                    status_val = metadata_pb2.ResourceStatus.NO_STATUS
                    status_name = "NO_STATUS"
                    error_msg = None
                else:
                    status_val = task_status.status.status
                    status_name = metadata_pb2.ResourceStatus.Status.Name(status_val)
                    error_msg = (
                        task_status.status.error_message
                        if hasattr(task_status.status, "error_message")
                        else None
                    )

                if status_val not in (
                    metadata_pb2.ResourceStatus.READY,
                    metadata_pb2.ResourceStatus.FAILED,
                    metadata_pb2.ResourceStatus.CANCELLED,
                ):
                    still_incomplete[res_key] = task_id
                    identifier = name if not variant else f"{name}:{variant}"
                    print(f"  {identifier} - Status: {status_name}")
                else:
                    if status_val != metadata_pb2.ResourceStatus.READY:
                        error_detail = f": {error_msg}" if error_msg else ""
                        identifier = name if not variant else f"{name}:{variant}"
                        print(
                            f"✗ {identifier} - "
                            f"Task {task_id} {status_name.lower()}{error_detail}"
                        )
                        raise RuntimeError(
                            f"Task {task_id} {status_name.lower()} for {identifier}{error_detail}"
                        )
                    else:
                        identifier = name if not variant else f"{name}:{variant}"
                        print(f"[OK] {identifier} - Deletion complete")

            incomplete = still_incomplete

            if incomplete:
                print(f"\nWaiting for {len(incomplete)} task(s)...")
                time.sleep(SECONDS_BETWEEN_STATUS_CHECKS)

        print("\nSuccessfully completed all tasks.")

    def update_resource_status(self, resource_table_row: ResourceTableRow):
        if not resource_table_row.get_status().is_finished():
            res = resource_table_row.resource.get(self._grpc_client)
            server_status = res.server_status
            resource_table_row.update_status(new_status=server_status.status)

            if server_status.error_info is not None:
                resource_table_row.update_status(
                    error=self._format_error_info(server_status.error_info)
                )
            else:
                resource_table_row.update_status(error=res.error)

    @staticmethod
    def _format_error_info(error_info: ErrorInfo):
        message = error_info.message
        reason = error_info.reason
        metadata = error_info.metadata

        formatted_metadata = "\n".join(
            [f"{key}: {value}" for key, value in metadata.items()]
        )
        return f"{reason}: {message}\n{formatted_metadata}"

    def all_statuses_finished(self) -> bool:
        return (
            len(self.unprocessed_resources) == 0 and len(self.display_table_list) == 0
        )

    def create_error_message(self):
        message = ""
        for resource_table_row in self.failed_list:
            status = resource_table_row.get_status()
            message += (
                f"{status.identifier()}: {resource_table_row.get_status_string()}"
                f" - {status.error}\n"
            )
        return message

    def display(self, host):
        if not self.unprocessed_resources:
            print("No resources to display")
            return

        console = Console(record=True)
        self.setup_display_resources()
        with Live(console=console, auto_refresh=False, screen=False) as live:
            # Used for updating loading dots based on the iteration number
            i = 0
            while True:
                self.update_display_data()
                display_table = self.create_display_table(i)
                live.update(display_table, refresh=True)

                if self.all_statuses_finished():
                    success_table = self.create_success_table(host)
                    failure_table = self.create_failure_table()
                    # Create the group only if there's at least one table
                    tables = [
                        table for table in [success_table, failure_table] if table
                    ]

                    if tables:
                        table_group = Group(*tables)  # Unpack the tables list
                        live.update(table_group, refresh=True)

                    if len(self.failed_list):
                        statuses = self.create_error_message()
                        sys.tracebacklimit = 0
                        raise Exception("Some resources failed to create\n" + statuses)
                    break

                i += 1
                time.sleep(SECONDS_BETWEEN_STATUS_CHECKS)

    def setup_display_resources(self):
        # Adding 25 rows from unprocessed_resources to display_table_list
        self.display_table_list = self.unprocessed_resources[:NUM_DISPLAY_ROWS]
        del self.unprocessed_resources[:NUM_DISPLAY_ROWS]

    def update_display_data(self):
        self._process_existing_display_rows()
        self._fill_display_rows_from_unprocessed_list()

    def _process_existing_display_rows(self):
        # We need to make a copy of the list because we are modifying it in the loop
        initial_display_table_list = self.display_table_list[:]
        for resource_table_row in initial_display_table_list:
            self.update_resource_status(resource_table_row)
            current_status = resource_table_row.get_status_string()
            if (
                current_status in {CREATED, READY}
                and resource_table_row not in self.success_list
            ):
                self.success_list.append(resource_table_row)
            elif (
                current_status == FAILED and resource_table_row not in self.failed_list
            ):
                self.failed_list.append(resource_table_row)

            # If the resource is complete, we should stop displaying after MAX_COMPLETED_TICKS
            if current_status not in {
                PENDING,
                RUNNING,
                NO_STATUS,
            }:
                resource_table_row.update_time_tick()
                if resource_table_row.get_time_ticks() > MAX_COMPLETED_TICKS:
                    self.display_table_list.remove(resource_table_row)

    # Fill the display_table_list with resources from unprocessed_resources
    def _fill_display_rows_from_unprocessed_list(self):
        while (
            len(self.display_table_list) < NUM_DISPLAY_ROWS
            and len(self.unprocessed_resources) > 0
        ):
            next_row = self.unprocessed_resources.pop(0)
            self.update_resource_status(next_row)
            self.add_resource_to_display_state(next_row)

    def add_resource_to_display_state(self, resource: ResourceTableRow):
        if (
            resource in self.success_list
            or resource in self.failed_list
            or resource in self.display_table_list
        ):
            raise ValueError("Resource should not be in success or failed list")
        current_status = resource.get_status_string()
        if current_status in {CREATED, READY}:
            self.success_list.append(resource)
        elif current_status == FAILED:
            self.failed_list.append(resource)
        elif current_status in {PENDING, NO_STATUS, RUNNING}:
            self.display_table_list.append(resource)
        else:
            raise ValueError(f"Invalid status {current_status}")

    def create_display_table(self, i):
        dots = "." * (1 + i % MAX_NUM_RUNNING_DOTS)
        title = f"[yellow]RUNNING{dots}[/]"
        table = self._create_table(title, "Status", True, None)
        for resource_table_row in self.display_table_list:
            status = resource_table_row.get_status()
            resource_type = resource_table_row.get_status_resourcetype()
            status_text = resource_table_row.get_status_string()
            table.add_row(
                Text(resource_type.to_string()),
                Text(status.display_name()),
                Text(status_text, style=self.STATUS_TO_COLOR[status_text]),
            )
        return table

    def _create_table(
        self, table_name, other_column, other_col_nowrap, other_col_style
    ):
        table = Table(
            title=table_name,
            title_justify="left",
            expand=True,
            show_header=True,
            header_style="bold",
            box=None,
        )
        table.add_column("Resource Type", width=15, no_wrap=True)
        table.add_column("Name", width=35)
        table.add_column(
            other_column, width=50, style=other_col_style, no_wrap=other_col_nowrap
        )
        return table

    def create_success_table(self, host):
        if len(self.success_list) == 0:
            return None
        resource_state = ResourceState()
        table = self._create_table("Completed Resources", "Dashboard Links", True, None)
        for resource_table_row in self.success_list:
            status = resource_table_row.get_status()
            resource_type = resource_table_row.get_status_resourcetype()
            name = resource_table_row.name
            url = resource_state.build_dashboard_url(
                host, resource_type, name, status.variant or ""
            )
            table.add_row(
                Text(resource_type.to_string()),
                Text(status.display_name()),
                Text(url, style="link", overflow="crop"),
            )
        return table

    def create_failure_table(self):
        if len(self.failed_list) == 0:
            return None
        table = self._create_table("Failed Resources", "Error", False, "red")
        for resource_table_row in self.failed_list:
            status = resource_table_row.get_status()
            resource_type = resource_table_row.get_status_resourcetype()
            name = resource_table_row.name
            error = f" {status.error}" if status.error else ""
            table.add_row(
                Text(resource_type.to_string()),
                Text(status.display_name()),
                Text(error, style="red", overflow="fold"),
            )
        return table
