import pytest
from blueapi.client.client import BlueapiClient, TaskRequest
from blueapi.client.event_bus import AnyEvent
from blueapi.core.bluesky_types import DataEvent
from blueapi.worker.event import TaskStatus, WorkerEvent, WorkerState
from blueapi.worker.task import Task

"""
1. Set username, password, and beamline settings in conftest.py
2. Login if BlueAPI server authentication is enabled.
"""


def _check_all_events(all_events: list[AnyEvent]):
    assert (
        isinstance(all_events[0], WorkerEvent) and all_events[0].task_status is not None
    )
    task_id = all_events[0].task_status.task_id
    # First event is WorkerEvent
    assert all_events[0] == WorkerEvent(
        state=WorkerState.RUNNING,
        task_status=TaskStatus(
            task_id=task_id,
            task_complete=False,
            task_failed=False,
        ),
    )

    assert all(isinstance(event, DataEvent) for event in all_events[1:-2]), (
        "Middle elements must be DataEvents."
    )

    # Last 2 events are WorkerEvent
    assert all_events[-2:] == [
        WorkerEvent(
            state=WorkerState.IDLE,
            task_status=TaskStatus(
                task_id=task_id,
                task_complete=False,
                task_failed=False,
            ),
        ),
        WorkerEvent(
            state=WorkerState.IDLE,
            task_status=TaskStatus(
                task_id=task_id,
                task_complete=True,
                task_failed=False,
            ),
        ),
    ]


@pytest.mark.parametrize(
    "device",
    [
        "sample_stage",
        "andor2_point",
        "andor2_det",
        "filter",
        "lab_stage",
        "angle_stage",
    ],
)
def test_device_present(client: BlueapiClient, device: str):
    assert client.get_device(device), f"{device} is not available"


@pytest.mark.parametrize("plan", ["count", "stxm_step", "stxm_fast"])
def test_spec_plan_available(
    client: BlueapiClient, task_definition: dict[str, Task], plan: str
):
    assert client.get_plan(plan), f"In {plan} is available"


@pytest.mark.parametrize("plan", ["count", "stxm_step", "stxm_fast"])
def test_spec_scan_task(
    client: BlueapiClient, task_definition: dict[str, Task], plan: str
):
    assert client.get_plan(plan), f"In {plan} is available"

    all_events: list[AnyEvent] = []

    def on_event(event: AnyEvent):
        all_events.append(event)

    client.run_task(
        TaskRequest(
            name=task_definition[plan].name,
            params=task_definition[plan].params,
            instrument_session="p99",
        ),
        on_event=on_event,
    )

    _check_all_events(all_events)

    assert client.get_state() is WorkerState.IDLE
