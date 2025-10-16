from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import ParamSpec, TypeVar

from bluesky import preprocessors as bpp
from bluesky.callbacks.fitting import PeakStats
from bluesky.plan_stubs import abs_set, read
from bluesky.plans import scan
from bluesky.utils import MsgGenerator, plan
from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor

from sm_bluesky.common.math_functions import cal_range_num
from sm_bluesky.common.plan_stubs import MotorTable
from sm_bluesky.log import LOGGER

from .fast_scan import fast_scan_1d


class StatPosition(tuple, Enum):
    """
    Data table to help access the fit data.\n
    Com: Centre of mass\n
    CEN: Peak position\n
    MIN: Minimum value\n
    MAX: Maximum value\n
    D: Differential\n
    """

    COM = ("stats", "com")
    CEN = ("stats", "cen")
    MIN = ("stats", "min")
    MAX = ("stats", "max")
    D_COM = ("derivative_stats", "com")
    D_CEN = ("derivative_stats", "cen")
    D_MIN = ("derivative_stats", "min")
    D_MAX = ("derivative_stats", "max")


P = ParamSpec("P")
T = TypeVar("T")
TCallable = Callable[
    P, T
]  # Type for callable functions with parameters P and return type T


def scan_and_move_to_fit_pos(func: TCallable) -> TCallable:
    """
    Wrapper to add a PeakStats callback before performing a scan
    and move to the fitted position after the scan.

    Parameters
    ----------
    funcs : TCallable
        The scan function to wrap.

    Returns
    -------
    TCallable
        The wrapped scan function.
    """

    @wraps(func)
    def inner(
        det: StandardReadable,
        motor: Motor,
        fitted_loc: StatPosition,
        detname_suffix: str,
        *args,
        **kwargs,
    ) -> MsgGenerator:
        ps = PeakStats(
            f"{motor.name}",
            f"{det.name}-{detname_suffix}",
            calc_derivative_and_stats=True,
        )
        yield from bpp.subs_wrapper(
            func(det, motor, fitted_loc, detname_suffix, *args, **kwargs),
            ps,
        )
        peak_position = get_stat_loc(ps, fitted_loc)

        LOGGER.info(f"Fit info {ps}")
        yield from abs_set(motor, peak_position, wait=True)

    return inner


@plan
@scan_and_move_to_fit_pos
def step_scan_and_move_fit(
    det: StandardReadable,
    motor: Motor,
    fitted_loc: StatPosition,
    detname_suffix: str,
    start: float,
    end: float,
    num: int,
) -> MsgGenerator:
    """
    Perform a step scan and move to the fitted position.

    Parameters
    ----------
    det : StandardReadable
        The detector to use for alignment.
    motor : Motor
        The motor to center.
    fitted_loc : StatPosition
        The fitted position to move to (see StatPosition).
    detname_suffix : str
        The suffix for the detector name.
    start : float
        The starting position for the scan.
    end : float
        The ending position for the scan.
    num : int
        The number of steps in the scan.

    Returns
    -------
    MsgGenerator
        A Bluesky generator for the scan.
    """
    LOGGER.info(
        f"Step scanning {motor.name} with {det.name}-{detname_suffix}\
            pro-scan move to {fitted_loc}"
    )
    return scan([det], motor, start, end, num=num)


@plan
@scan_and_move_to_fit_pos
def fast_scan_and_move_fit(
    det: StandardReadable,
    motor: Motor,
    fitted_loc: StatPosition,
    detname_suffix: str,
    start: float,
    end: float,
    motor_speed: float | None = None,
) -> MsgGenerator:
    """Does a fast non-stopping scan and move to the fitted position.

    Parameters
    ----------
    det: StandardReadable,
        Detector to be use for alignment.
    motor: Motor
        Motor devices that is being centre.
    fitted_loc: StatPosition
        Which fitted position to move to see StatPosition.
    detname_suffix: Str
        Name of the fitted axis within the detector
    start: float,
        Starting position for the scan.
    end: float,
        Ending position for the scan.
    motor_speed: Optional[float] = None,
        Speed of the motor.
    """
    LOGGER.info(
        f"Fast scanning {motor.hints} with {det.name}-{detname_suffix}\
              pro-scan move to {fitted_loc}"
    )
    return fast_scan_1d(
        dets=[det], motor=motor, start=start, end=end, motor_speed=motor_speed
    )


def get_stat_loc(ps: PeakStats, loc: StatPosition) -> float:
    """Helper to check the fit was done correctly and
    return requested stats position."""
    peak_stat = ps[loc.value[0]]
    if not peak_stat:
        raise ValueError("Fitting failed, check devices name are correct.")
    peak_stat = peak_stat._asdict()

    if not peak_stat["fwhm"]:
        raise ValueError("Fitting failed, no peak within scan range.")

    stat_pos = peak_stat[loc.value[1]]
    return stat_pos if isinstance(stat_pos, float) else stat_pos[0]


@plan
def align_slit_with_look_up(
    motor: Motor,
    size: float,
    slit_table: dict[str, float],
    det: StandardReadable,
    centre_type: StatPosition,
) -> MsgGenerator:
    """Perform a step scan with therange and starting motor position
      given/calculated by using a look up table(dictionary).
      Move to the peak position after the scan and update the lookup table.

    Parameters
    ----------
    motor: Motor
        Motor devices that is being centre.
    size: float,
        The size/name in the motor_table.
    motor_table: dict[str, float],
        Look up table for motor position, the str part should be the size of
        the slit in um.
    det: StandardReadable,
        Detector to be use for alignment.
    centre_type: StatPosition
        Which fitted position to move to see StatPosition.
    """
    MotorTable.model_validate(slit_table)
    if str(int(size)) in slit_table:
        start_pos, end_pos, num = cal_range_num(
            cen=slit_table[str(size)], range=size / 1000 * 3, size=size / 5000.0
        )
    else:
        raise ValueError(f"Size of {size} is not in {slit_table.keys}")
    yield from step_scan_and_move_fit(
        det=det,
        motor=motor,
        start=start_pos,
        detname_suffix="value",
        end=end_pos,
        fitted_loc=centre_type,
        num=num,
    )
    temp = yield from read(motor.user_readback)
    slit_table[str(size)] = temp[f"{motor.name}"]["value"]
