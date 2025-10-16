from collections.abc import Hashable

from bluesky.plan_stubs import abs_set, mv, wait
from dodal.beamlines.i10 import DetSlits, I10Slits
from dodal.common import inject
from dodal.common.types import MsgGenerator
from dodal.devices.i10.rasor.rasor_motors import Diffractometer
from dodal.devices.motors import XYZStage
from dodal.devices.slits import Slits
from ophyd_async.core import StandardReadable

from sm_bluesky.common.math_functions import cal_range_num
from sm_bluesky.common.plan_stubs import move_motor_with_look_up
from sm_bluesky.common.plans import (
    StatPosition,
    align_slit_with_look_up,
    step_scan_and_move_fit,
)
from sm_bluesky.log import LOGGER

"""I10 has fix/solid slit on a motor, this store the rough motor opening
 position against slit size in um"""

DSD = {"5000": 14.3, "1000": 19.3, "500": 26.5, "100": 29.3, "50": 34.3}
DSU = {"5000": 16.7, "1000": 21.7, "500": 25.674, "100": 31.7, "50": 36.7}


def move_dsu(
    size: float,
    slit_table: dict[str, float] = DSU,
    use_motor_position: bool = False,
    wait: bool = True,
    group: Hashable | None = None,
    det_slits: DetSlits = inject("det_slits"),
) -> MsgGenerator:
    """Move up stream detector slit either by it size in slit motor table or by motor
    position."""
    yield from move_motor_with_look_up(
        slit=det_slits.upstream,
        size=size,
        motor_table=slit_table,
        use_motor_position=use_motor_position,
        wait=wait,
        group=group,
    )


def move_dsd(
    size: float,
    slit_table: dict[str, float] = DSD,
    use_motor_position: bool = False,
    wait: bool = True,
    group: Hashable | None = None,
    det_slits: DetSlits = inject("det_slits"),
) -> MsgGenerator:
    """Move down stream detector slit either by it size in slit motor table or by motor
    position."""
    yield from move_motor_with_look_up(
        slit=det_slits.downstream,
        size=size,
        motor_table=slit_table,
        use_motor_position=use_motor_position,
        wait=wait,
        group=group,
    )


def align_dsu(
    size: float,
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_slits: DetSlits = inject("det_slits"),
) -> MsgGenerator:
    """Align the up stream detector slit"""
    yield from align_slit_with_look_up(
        motor=det_slits.upstream,
        size=size,
        slit_table=DSU,
        det=det,
        centre_type=StatPosition.COM,
    )


def align_dsd(
    size: float,
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_slits: DetSlits = inject("det_slits"),
) -> MsgGenerator:
    """Align the down stream detector slit"""
    yield from align_slit_with_look_up(
        motor=det_slits.downstream,
        size=size,
        slit_table=DSD,
        det=det,
        centre_type=StatPosition.COM,
    )


def align_pa_slit(
    dsd_size: float,
    dsu_size: float,
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    det_slits: DetSlits = inject("det_slits"),
) -> MsgGenerator:
    """Align both detector slits"""
    yield from move_dsd(5000, wait=True, det_slits=det_slits)
    yield from align_dsu(dsu_size, det, det_slits)
    yield from align_dsd(dsd_size, det, det_slits)


def align_s5s6(
    det: StandardReadable = inject("rasor_femto_pa_scaler_det"),
    slits: I10Slits = inject("slits"),
    diffractometer: Diffractometer = inject("diffractometer"),
    sample_stage: XYZStage = inject("sample_stage"),
) -> MsgGenerator:
    """
    Plan to align the s5s6 slits with the straight through beam
    and RASOR detector, it define where all the motor should be and call
    align slits

    Parameters
    ----------
    det (optional): StandardReadable
        Detector that use for the alignments, default is rasor photodiode.
    slits (optional): I10Slits
        Slits used for alignment.
    diffractometer (optional): Diffractometer
        Diffractometer to move out of beam.
    sample_stage (optional): XYZStage:
        sample stage to move out of beam.
    """
    yield from move_to_direct_beam_position(diffractometer, sample_stage)

    yield from align_slit(
        det=det,
        slit=slits.s5,
        x_scan_size=0.1,
        x_final_size=0.65,
        x_range=2,
        x_open_size=2,
        x_cen=0,
        y_scan_size=0.1,
        y_final_size=1.3,
        y_open_size=4,
        y_range=2,
        y_cen=0,
    )
    LOGGER.info("Aligning s6")
    yield from align_slit(
        det=det,
        slit=slits.s6,
        x_scan_size=0.1,
        x_final_size=0.45,
        x_range=2,
        x_open_size=4,
        x_cen=0,
        y_scan_size=0.1,
        y_final_size=0.6,
        y_open_size=4,
        y_range=2,
        y_cen=0,
    )


def align_slit(
    det: StandardReadable,
    slit: Slits,
    x_scan_size: float,
    x_final_size: float,
    x_open_size: float,
    y_scan_size: float,
    y_final_size: float,
    y_open_size: float,
    x_range: float,
    x_cen: float,
    y_range: float,
    y_cen: float,
    centre_type: StatPosition = StatPosition.COM,
) -> MsgGenerator:
    """
    Plan to align a pair of standard x-y slits,
    it does a pair of slits scan and go to the centre of mass by default.

    Parameters
    ----------
    det: StandardReadable
        Detector to use for alignment.
    slit: Slits,
        x-y slits.
    x_scan_size: float,
        The size of the x slit use for alignment.
    x_final_size: float,
        The size of the x slit to set to after alignment.
    x_open_size: float,
        The size of the x slit during y slit alignment.
    y_scan_size: float,
        The size of the y slit use for alignment.
    y_final_size: float,
        The size of the y slit to set to after alignment.
    y_open_size: float,
        The size of the y slit during x slit alignment.
    x_range: float,
        The x slit range, range is the distant from the centre.
        e.g. a range of 1 with centre at 0 will cover -1 to 1.
    x_cen: float,
        The best guess of x slit centre.
    y_range: float,
        The y slit range.
    y_cen: float,
        The best guess of y slit centre.
    centre_type: StatPosition = StatPosition.COM
        Where to move the slits, it goes to centre of mass by default.
        see StatPosition for other options.
    """
    group_wait = "slits group"
    yield from abs_set(slit.x_gap, x_scan_size, group=group_wait)
    yield from abs_set(slit.y_gap, y_open_size, group=group_wait)
    LOGGER.info(f"Moving to starting position for {slit.x_centre.name} alignment.")
    yield from wait(group=group_wait)
    yield from mv(slit.y_centre, y_cen, group=group_wait)  # type: ignore
    start_pos, end_pos, num = cal_range_num(x_cen, x_range, x_scan_size)
    yield from step_scan_and_move_fit(
        det=det,
        motor=slit.x_centre,
        detname_suffix="value",
        start=start_pos,
        end=end_pos,
        fitted_loc=centre_type,
        num=num,
    )

    yield from abs_set(slit.y_gap, y_scan_size, group=group_wait)
    yield from abs_set(slit.x_gap, x_open_size, group=group_wait)
    LOGGER.info(f"Moving to starting position for {slit.y_centre.name} alignment.")
    yield from wait(group=group_wait)
    start_pos, end_pos, num = cal_range_num(y_cen, y_range, y_scan_size)
    yield from step_scan_and_move_fit(
        det=det,
        motor=slit.y_centre,
        detname_suffix="value",
        start=start_pos,
        end=end_pos,
        fitted_loc=centre_type,
        num=num,
    )
    yield from abs_set(slit.x_gap, x_final_size, group=group_wait)
    yield from abs_set(slit.y_gap, y_final_size, group=group_wait)
    yield from wait(group=group_wait)


def move_to_direct_beam_position(
    diffractometer: Diffractometer = inject("diffractometer"),
    sample_stage: XYZStage = inject("sample_stage"),
) -> MsgGenerator:
    """Remove everything in the way of the beam"""
    group_wait = "diff group A"
    yield from abs_set(diffractometer.tth, 0, group=group_wait)
    yield from abs_set(diffractometer.th, 0, group=group_wait)
    yield from abs_set(sample_stage.y, -3, group=group_wait)
    yield from wait(group=group_wait)
