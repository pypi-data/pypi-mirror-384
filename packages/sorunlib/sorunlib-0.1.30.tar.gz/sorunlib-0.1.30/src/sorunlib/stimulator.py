import time
import sorunlib as run
from sorunlib._internal import check_response, protect_shutdown, stop_smurfs

ID_SHUTTER = 1


def _open_shutter():
    """Open the shutter of the stimulator"""
    ds = run.CLIENTS['stimulator']['ds378']
    resp = ds.set_relay(relay_number=ID_SHUTTER, on_off=1)
    check_response(ds, resp)

    time.sleep(3)


def _close_shutter():
    """Close the shutter of the stimulator"""
    ds = run.CLIENTS['stimulator']['ds378']
    resp = ds.set_relay(relay_number=ID_SHUTTER, on_off=0)
    check_response(ds, resp)

    time.sleep(3)


def _setup():
    # Open shutter
    _open_shutter()

    # Acceleration / Decceleration configuration
    blh = run.CLIENTS['stimulator']['blh']
    resp = blh.set_values(accl_time=10, decl_time=10)
    check_response(blh, resp)


@protect_shutdown
def _stop():
    blh = run.CLIENTS['stimulator']['blh']

    # Stop rotation
    resp = blh.stop_rotation()
    check_response(blh, resp)
    time.sleep(10)

    # Close shutter
    _close_shutter()


def calibrate_tau(duration_step=20,
                  speeds_rpm=[225, 495, 945, 1395, 1845, 2205],
                  forward=True, do_setup=True, stop=True,
                  downsample_factor=8, filter_disable=False, filter_order=None, filter_cutoff=None):
    """Time constant calibration using the stimulator.

    Parameters
    ----------
    duration_step : float, optional
        Duration of each step of time constant measurement in sec, default to 20 sec.
    speeds_rpm : list of float, optional
        List of chopper rotation speed in RPM for each step. Defaults to [225, 495, 945, 1395, 1845, 2205].
    forward : bool, optional
        Chopper rotation direction. If True, the chopper rotates clockwise
        when viewed from the receiver toward the stimulator. Defaults to True.
    do_setup : bool, optional
        Do initial setup (i.e. open shutter, set acceleration, start rotation) if True. Defaults to True.
    stop : bool, optional
        Stop the rotation and close the shutter if True. Defaults to True.
    downsample_factor : int, optional
        Downsample factor for SMuRF. Defaults to 8.
    filter_disable : bool, optional
        If True, will disable the downsample filter before streaming. Defaults to False.
    filter_order : int, optional
        Order of the downsample filter for SMuRF. Defaults to None.
        If None is passed, the pysmurf default(normally 4) will be used.
    filter_cutoff : float, optional
        The cutoff frequency in Hz for the downsample filter for SMuRF. Defaults to None.
        If None is passed, will be (63/200)*sampling_rate.
    """

    blh = run.CLIENTS['stimulator']['blh']
    downsample_factor = int(downsample_factor)

    try:
        tag = f'stimulator,time_constant,downsample_factor_{downsample_factor:.0f}'
        if filter_disable is True:
            tag += ',filter_disabled'
        else:
            if filter_cutoff is None:
                filter_cutoff = int(63 / 200 * 4000 / downsample_factor)
            tag += f',filter_cutoff_{filter_cutoff:.0f}'

            if filter_order is not None and filter_order != 4:
                tag += f',filter_order_{filter_order:.0f}'

        run.smurf.stream('on',
                         tag=tag,
                         subtype='cal',
                         downsample_factor=downsample_factor,
                         filter_disable=filter_disable,
                         filter_order=filter_order,
                         filter_cutoff=filter_cutoff)

        if do_setup:
            _setup()
            # Rotation setting
            resp = blh.set_values(speed=speeds_rpm[0])
            check_response(blh, resp)

            resp = blh.start_rotation(forward=forward)
            check_response(blh, resp)

            speeds_rpm = speeds_rpm[1:]

            # First data point
            time.sleep(duration_step)

        for speed_rpm in speeds_rpm:
            resp = blh.set_values(speed=speed_rpm)
            check_response(blh, resp)

            time.sleep(duration_step)
    finally:
        stop_smurfs()

        if stop:
            _stop()


def calibrate_gain(duration=60, speed_rpm=90,
                   forward=True, do_setup=True, stop=True,
                   downsample_factor=8, filter_disable=False, filter_order=None, filter_cutoff=None):
    """Gain calibration with the stimulator

    Parameters
    ----------
    duration : float, optional
        Duration of the gain calibration in sec, default to 60 sec.
    speed_rpm : float, optional
        Rotation speed of the chopper wheel in RPM, default to 90 RPM.
    forward : bool, optional
        Chopper rotation direction. If True, the chopper rotates clockwise
        when viewed from the receiver toward the stimulator. Defaults to True.
    do_setup : bool, optional
        Do initial setup (i.e. open shutter, set acceleration, start rotation) if True.
        Defaults to True.
    stop : bool, optional
        Stop the rotation and close the shutter if True. Defaults to True.
    downsample_factor : int, optional
        Downsample factor for SMuRF. Defaults to 8.
    filter_disable : bool, optional
        If True, will disable the downsample filter before streaming. Defaults to False.
    filter_order : int, optional
        Order of the downsample filter for SMuRF. Defaults to None.
        If None is passed, the pysmurf default(normally 4) will be used.
    filter_cutoff : float, optional
        The cutoff frequency in Hz for the downsample filter for SMuRF. Defaults to None.
        If None is passed, will be (63/200)*sampling_rate.
    """

    blh = run.CLIENTS['stimulator']['blh']
    downsample_factor = int(downsample_factor)

    try:
        resp = blh.set_values(speed=speed_rpm)
        check_response(blh, resp)

        if do_setup:
            _setup()
            # Rotation setting
            resp = blh.start_rotation(forward=forward)
            check_response(blh, resp)

        # Sleep for rotation stabilization
        time.sleep(10)

        tag = f'stimulator,gain,downsample_factor_{downsample_factor:.0f}'
        if filter_disable is True:
            tag += ',filter_disabled'
        else:
            if filter_cutoff is None:
                filter_cutoff = int(63 / 200 * 4000 / downsample_factor)
            tag += f',filter_cutoff_{filter_cutoff:.0f}'
            if filter_order is not None and filter_order != 4:
                tag += f',filter_order_{filter_order:.0f}'

        run.smurf.stream('on',
                         tag=tag,
                         subtype='cal',
                         downsample_factor=downsample_factor,
                         filter_disable=filter_disable,
                         filter_order=filter_order,
                         filter_cutoff=filter_cutoff)

        # Data taking
        time.sleep(duration)
    finally:
        stop_smurfs()

        if stop:
            _stop()


def calibrate_gain_tau(duration_gain=60, duration_tau=10, duration_stabilization=10,
                       speed_rpm_gain=90, speeds_rpm_tau=[225, 495, 945, 1395, 1845, 2205],
                       forward=True,
                       downsample_factor=8, filter_disable=False, filter_order=None, filter_cutoff=None):
    """Gain and time-constant calibration at the same time

    Parameters
    ----------
    duration_gain : float, optional
        Duration of the gain calibration in sec, default to 60 sec.
    duration_tau : float, optional
        Duration of each step of time constant measurement in sec, default to 10 sec.
    duration_stabilization: float, optional
        Duration to stabilize the chopper wheel speed in sec, default to 10 sec.
    speed_rpm_gain : float, optional
        Rotation speed of the chopper wheel in RPM for gain calibration, default to 90 RPM.
    speeds_rpm_tau : list of float, optional
        List of chopper rotation speed in RPM for each step for time-constant calibration.
        Defaults to [225, 495, 945, 1395, 1845, 2205].
    forward : bool, optional
        Chopper rotation direction. If True, the chopper rotates clockwise
        when viewed from the receiver toward the stimulator. Defaults to True.
    downsample_factor : int, optional
        Downsample factor for SMuRF. Defaults to 8.
    filter_disable : bool, optional
        If True, will disable the downsample filter before streaming. Defaults to False.
    filter_order : int, optional
        Order of the downsample filter for SMuRF. Defaults to None.
        If None is passed, the pysmurf default(normally 4) will be used.
    filter_cutoff : float, optional
        The cutoff frequency in Hz for the downsample filter for SMuRF. Defaults to None.
        If None is passed, will be (63/200)*sampling_rate.
    """

    blh = run.CLIENTS['stimulator']['blh']
    downsample_factor = int(downsample_factor)

    try:
        # Shutter and chopper setup
        resp = blh.set_values(speed=speed_rpm_gain)
        check_response(blh, resp)
        _setup()

        # Rotation setting
        resp = blh.start_rotation(forward=forward)
        check_response(blh, resp)

        # Sleep for rotation stabilization
        time.sleep(duration_stabilization)

        # Start data taking
        tag = f'stimulator,gain_and_timeconstant,downsample_factor_{downsample_factor:.0f}'
        if filter_disable is True:
            tag += ',filter_disabled'
        else:
            if filter_cutoff is None:
                filter_cutoff = int(63 / 200 * 4000 / downsample_factor)
            tag += f',filter_cutoff_{filter_cutoff:.0f}'
            if filter_order is not None and filter_order != 4:
                tag += f',filter_order_{filter_order:.0f}'

        run.smurf.stream('on',
                         tag=tag,
                         subtype='cal',
                         downsample_factor=downsample_factor,
                         filter_disable=filter_disable,
                         filter_order=filter_order,
                         filter_cutoff=filter_cutoff)

        time.sleep(duration_gain)

        for speed_rpm in speeds_rpm_tau:
            resp = blh.set_values(speed=speed_rpm)
            check_response(blh, resp)

            time.sleep(duration_stabilization)
            time.sleep(duration_tau)
    finally:
        stop_smurfs()

        _stop()
