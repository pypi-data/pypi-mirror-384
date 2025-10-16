import sorunlib as run
from sorunlib._internal import check_response, stop_smurfs


def _get_direction():
    """Get the rotational direction ('cw' or 'ccw') of the HWP. The direction
    is determined in part by the configuration of the HWP supervisor agent. For
    details see the `HWP Supervisor agent docs <docs_>`_.

    * 'cw' is clockwise as seen from the sky to window.
    * 'ccw' is counter-clockwise as seen from the sky to window.

    Returns:
        str: The direction of the HWP, either 'cw' or 'ccw'.

    Raises:
        RuntimeError: If the direction is not either 'cw' or 'ccw'.

    .. _docs: https://socs.readthedocs.io/en/main/agents/hwp_supervisor_agent.html

    """
    hwp = run.CLIENTS['hwp']
    resp = hwp.monitor.status()
    direction = resp.session['data']['hwp_state']['direction']

    if direction not in ['cw', 'ccw']:
        raise RuntimeError("The HWP direction is unknown. Aborting...")

    return direction


# Public API
def set_freq(freq, timeout=None):
    """Set the rotational frequency of the HWP.

    Args:
        freq (float): Target frequency to rotate the HWP in Hz. This is a
            *signed float*, the meaning of which depends on the OCS site
            configuration. For details see the `documentation for the HWP
            Supervisor Agent <docs_>`_.
        timeout (float, optional): Duration, in seconds, to wait for the
            operation to complete. An exception will be raised if this timeout
            is exceeded.

    .. _docs: https://socs.readthedocs.io/en/main/agents/hwp_supervisor_agent.html

    """
    hwp = run.CLIENTS['hwp']
    if timeout is None:
        resp = hwp.pid_to_freq(target_freq=freq)
    else:
        hwp.pid_to_freq.start(target_freq=freq)
        resp = hwp.pid_to_freq.wait(timeout=timeout)
    check_response(hwp, resp)


def spin_up(freq):
    """Spin up the HWP while streaming data.

    Args:
        freq (float): Target frequency to rotate the HWP in Hz. This is a
            *signed float*, the meaning of which depends on the OCS site
            configuration. For details see the `documentation for the HWP
            Supervisor Agent <docs_>`_.

    .. _docs: https://socs.readthedocs.io/en/main/agents/hwp_supervisor_agent.html

    """
    hwp = run.CLIENTS['hwp']

    try:
        run.smurf.stream('on', subtype='cal', tag='hwp_spin_up')
        resp = hwp.enable_driver_board()
        check_response(hwp, resp)
        run.hwp.set_freq(freq=freq, timeout=1800)
    finally:
        stop_smurfs()


def spin_down(active=True, brake_voltage=None):
    """Spin down the HWP while streaming data.

    Args:
        active (bool, optional): If True, actively try to stop the HWP by
            applying the brake. If False, simply turn off the PMX power and wait
            for it to spin down on its own. Defaults to True.
        brake_voltage (float, optional): Voltage used when actively stopping
            the HWP. Only considered when active is True.

    """
    hwp = run.CLIENTS['hwp']

    try:
        run.smurf.stream('on', subtype='cal', tag='hwp_spin_down')
        run.hwp.stop(active=active,
                     brake_voltage=brake_voltage)
        resp = hwp.disable_driver_board()
        check_response(hwp, resp)
    finally:
        stop_smurfs()


def stop(active=True, brake_voltage=None):
    """Stop the HWP.

    Args:
        active (bool, optional): If True, actively try to stop the HWP by
            applying the brake. If False, simply turn off the PMX power and wait
            for it to spin down on its own. Defaults to True.
        brake_voltage (float, optional): Voltage used when actively stopping
            the HWP. Only considered when active is True.

    """
    hwp = run.CLIENTS['hwp']

    print('Stopping HWP and waiting for it to spin down.')
    if active:
        if brake_voltage is None:
            resp = hwp.brake()
        else:
            resp = hwp.brake(brake_voltage=brake_voltage)
        check_response(hwp, resp)
    else:
        resp = hwp.pmx_off(wait_stop=True)
        check_response(hwp, resp)
