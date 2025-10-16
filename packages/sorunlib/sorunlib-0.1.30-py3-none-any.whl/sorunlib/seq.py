import datetime as dt
import time

import sorunlib as run

from sorunlib.commands import _timestamp_to_utc_datetime
from sorunlib._internal import check_response, check_started, monitor_process, protect_shutdown, stop_smurfs


OP_TIMEOUT = 60


@protect_shutdown
def _stop_scan():
    acu = run.CLIENTS['acu']

    print("Stopping scan.")
    stop_smurfs()

    # Stop motion
    acu.generate_scan.stop()
    print("Waiting for telescope motion to stop.")
    resp = acu.generate_scan.wait(timeout=OP_TIMEOUT)
    check_response(acu, resp)
    print("Scan finished.")


def scan(description, stop_time, width, az_drift=0, type=1, el_amp=None,
         tag=None, subtype=None, min_duration=None):
    """Run a constant elevation scan, collecting detector data.

    Args:
        description (str): Description of the field/object being scanned.
        stop_time (str): Time in ISO format to scan until, i.e.
            "2022-06-21T15:58:00"
        width (float): Scan width in azimuth. The scan will start at the
            current position and move in the positive azimuth direction.
        az_drift (float): Drift velocity in deg/s, causing scan extrema to move
            accordingly.
        type (int): Scan type.  Possible values are 1, 2, or 3.
        el_amp (float): For type 3 scans, the amplitude (half
            peak-to-peak) for the elevation oscillation, in degrees.
            Must be specified if type=3 (but can be zero).
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation. Passed through to the smurf stream command.
        subtype (str, optional): Operation subtype used to tag the stream.
        min_duration (float, optional): Minimum duration required to scan,
            specified in seconds. If not enough time exists between now and the
            ``stop_time`` the scan is not executed. Defaults to None.

    """
    now = dt.datetime.now(dt.timezone.utc)
    scan_stop = _timestamp_to_utc_datetime(stop_time)

    # Check stop time has not already passed
    if now > scan_stop:
        return

    # Check there is enough time to perform scan
    if min_duration is not None:
        start_by_time = scan_stop - dt.timedelta(seconds=min_duration)
        if now > start_by_time:
            return

    # It is an error to not declare el_amp when you specify type 3 scan.
    assert (type != 3 or el_amp is not None)

    acu = run.CLIENTS['acu']

    try:
        # Enable SMuRF streams
        run.smurf.stream('on', subtype=subtype, tag=tag)

        # Grab current telescope position
        resp = acu.monitor.status()
        az = resp.session['data']['StatusDetailed']['Azimuth current position']
        el = resp.session['data']['StatusDetailed']['Elevation current position']

        if type == 3:
            el1 = el - el_amp
            el2 = el + el_amp
        else:
            el1 = el2 = el

        # Start telescope motion
        # az_speed and az_accel assumed from ACU defaults
        # Can be modified by acu.set_scan_params()
        resp = acu.generate_scan.start(az_endpoint1=az,
                                       az_endpoint2=az + width,
                                       el_endpoint1=el1,
                                       el_endpoint2=el2,
                                       el_speed=0,
                                       az_drift=az_drift,
                                       type=type)
        check_started(acu, resp)

        # Wait until stop time
        monitor_process(acu, 'generate_scan', stop_time)
    finally:
        _stop_scan()


def el_nod(el1, el2, num=5, pause=5):
    """Perform a set of elevation nods.

    Elevation nods will be peformed at the current azimuth, and will start from
    and return to the current elevation. The nod first moves to ``el1``,
    pauses, then moves to ``el2``, pauses, and then repeats for the
    specified number of iterations.

    Args:
        el1 (float): First elevation to move to during the nod.
        el2 (float): Second elevation to move to during the nod.
        num (int): Number of nods to peform. Defaults to 5.
        pause (float): Length of pause, in seconds, at each elevation. Defaults
            to 5 seconds.

    """
    acu = run.CLIENTS['acu']

    try:
        # Enable SMuRF streams
        run.smurf.stream('on', subtype='cal', tag='el_nods')

        # Grab current telescope position
        resp = acu.monitor.status()
        init_az = resp.session['data']['StatusDetailed']['Azimuth current position']
        init_el = resp.session['data']['StatusDetailed']['Elevation current position']

        # Perform nods
        for x in range(num):
            run.acu.move_to(az=init_az, el=el1)
            time.sleep(pause)
            run.acu.move_to(az=init_az, el=el2)
            time.sleep(pause)
        else:
            # Return to initial position
            run.acu.move_to(az=init_az, el=init_el)
    finally:
        stop_smurfs()
