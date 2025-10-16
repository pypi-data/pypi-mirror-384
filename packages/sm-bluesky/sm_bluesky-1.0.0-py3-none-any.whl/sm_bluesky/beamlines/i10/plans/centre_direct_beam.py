from collections.abc import Hashable

import bluesky.plan_stubs as bps
from dodal.common import inject
from dodal.common.types import MsgGenerator
from dodal.devices.i10.rasor.rasor_motors import Diffractometer
from dodal.devices.motors import XYZStage
from ophyd_async.core import StandardReadable

from sm_bluesky.beamlines.i10.configuration.default_setting import (
    RASOR_DEFAULT_DET_NAME_EXTENSION,
)
from sm_bluesky.common.plans import StatPosition, step_scan_and_move_fit


def centre_tth(
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_name: str = RASOR_DEFAULT_DET_NAME_EXTENSION,
    start: float = -1,
    end: float = 1,
    num: int = 21,
    diffractometer: Diffractometer = inject("diffractometer"),
) -> MsgGenerator:
    """Centre two theta using Rasor dector."""

    yield from step_scan_and_move_fit(
        det=det,
        motor=diffractometer.tth,
        start=start,
        end=end,
        num=num,
        detname_suffix=det_name,
        fitted_loc=StatPosition.CEN,
    )


def centre_alpha(
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_name: str = RASOR_DEFAULT_DET_NAME_EXTENSION,
    start: float = -0.8,
    end: float = 0.8,
    num: int = 21,
    diffractometer: Diffractometer = inject("diffractometer"),
) -> MsgGenerator:
    """Centre rasor alpha using Rasor dector."""
    yield from step_scan_and_move_fit(
        det=det,
        motor=diffractometer.alpha,
        start=start,
        end=end,
        num=num,
        detname_suffix=det_name,
        fitted_loc=StatPosition.CEN,
    )


def centre_det_angles(
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_name: str = RASOR_DEFAULT_DET_NAME_EXTENSION,
    diffractometer: Diffractometer = inject("diffractometer"),
) -> MsgGenerator:
    """Centre both two theta and alpha angle on Rasor"""
    yield from centre_tth(det, det_name, diffractometer=diffractometer)
    yield from centre_alpha(det, det_name, diffractometer=diffractometer)


def move_pin_origin(
    wait: bool = True,
    group: Hashable | None = None,
    sample_stage: XYZStage = inject("sample_stage"),
) -> MsgGenerator:
    """Move the point to the centre of rotation."""

    if wait and group is None:
        group = "move_pin_origin"
    yield from bps.abs_set(sample_stage.x, 0, wait=False, group=group)
    yield from bps.abs_set(sample_stage.y, 0, wait=False, group=group)
    yield from bps.abs_set(sample_stage.z, 0, wait=False, group=group)
    if wait:
        yield from bps.wait(group=group)
