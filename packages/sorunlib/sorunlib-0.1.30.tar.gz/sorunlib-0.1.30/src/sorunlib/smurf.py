"""This module is responsible for commanding all active pysmurf-controller
agents.

If a SMuRF fails to perform an operation it will be dropped from the global
``CLIENTS`` list, removing it from further use during that schedule. If the
number of active SMuRFs falls below the configured ``smurf_failure_threshold``
an exception will be raised, halting observations.

:func:`initialize() <sorunlib.__init__.initialize>` must be run to re-add
previously failed SMuRFs to the ``CLIENTS`` list.

"""

import time

from ocs.client_http import ControlClientError

import sorunlib as run
from sorunlib._internal import check_response, check_started

# Timing between commanding separate SMuRF Controllers
# Yet to be determined in the field. Eventually might need this to be unique
# per operation. Also, move to configuration file once sorunlib has one.
CRYO_WAIT = 120


def _wait_for_cryo(time_):
    if time_ is None:
        wait = CRYO_WAIT
    else:
        wait = time_
    time.sleep(wait)


def _check_smurf_threshold():
    cfg = run.config.load_config()
    threshold = cfg['smurf_failure_threshold']
    remaining = len(run.CLIENTS['smurf'])
    if remaining < threshold:
        error = 'Functional SMuRF count below failure threshold ' + \
                f'({remaining} < {threshold}).'
        raise RuntimeError(error)


def _run_op(operation, concurrent, settling_time, **kwargs):
    """Run operation across all active SMuRF controllers.

    Additional kwargs are passed directly to the ``.start()`` call.

    Args:
        operation (str): Operation name.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. If None, defaults to a fixed wait
            time of 120 seconds.

    """
    clients_to_remove = []

    # Start operation
    for smurf in run.CLIENTS['smurf']:
        op = smurf.__getattribute__(operation)
        op.start(**kwargs)
        # Run in series
        if not concurrent:
            resp = op.wait()
            try:
                check_response(smurf, resp)
            except RuntimeError as e:
                print(f"Failed to perform {operation} on {smurf}, removing from targets list.")
                print(e)
                clients_to_remove.append(smurf)

            # Allow cryo to settle
            _wait_for_cryo(settling_time)

    # Run in parallel
    if concurrent:
        for smurf in run.CLIENTS['smurf']:
            op = smurf.__getattribute__(operation)
            resp = op.wait()
            try:
                check_response(smurf, resp)
            except RuntimeError as e:
                print(f"Failed to perform {operation} on {smurf}, removing from targets list.")
                print(e)
                clients_to_remove.append(smurf)

    # Remove failed SMuRF clients
    for client in clients_to_remove:
        run.CLIENTS['smurf'].remove(client)

    # Check if enough SMuRFs remain
    _check_smurf_threshold()


def set_targets(targets):
    """Set the target pysmurf-controller Agents that sorunlib will command.

    Args:
        targets (list): List of pysmurf-controller instance-ids to send future
            commands to. This must be a subset of the currently active clients
            list.

    Notes:
        This modifies the global ``sorunlib.CLIENTS`` list.

    """
    _smurf_clients = []
    for smurf in run.CLIENTS['smurf']:
        if smurf.instance_id in targets:
            _smurf_clients.append(smurf)

    run.CLIENTS['smurf'] = _smurf_clients


def bias_step(tag=None, concurrent=True, settling_time=None):
    """Perform a bias step on all SMuRF Controllers.

    Args:
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. If None, defaults to a fixed wait
            time of 120 seconds.

    """
    _run_op('take_bias_steps',
            concurrent=concurrent,
            settling_time=settling_time,
            tag=tag)


def iv_curve(tag=None, iv_kwargs=None, concurrent=True, settling_time=None):
    """Perform an iv curve on all SMuRF Controllers.

    Args:
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation.
        iv_kwargs (dict, optional): Additional keyword arguments to pass to
            ``take_iv``.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. If None, defaults to a fixed wait
            time of 120 seconds.

    """
    _run_op('take_iv',
            concurrent=concurrent,
            settling_time=settling_time,
            tag=tag,
            kwargs=iv_kwargs)


def uxm_setup(concurrent=True, settling_time=0):
    """Perform first-time setup procedure for a UXM.

    Args:
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('uxm_setup',
            concurrent=concurrent,
            settling_time=settling_time)


def uxm_relock(test_mode=False, concurrent=True, settling_time=0):
    """Relocks detectors to existing tune if setup has already been run.

    Args:
        test_mode (bool): Run uxm_setup() task in test_mode, removing emulated
            wait times.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    if test_mode:
        _run_op('uxm_relock',
                concurrent=concurrent,
                settling_time=settling_time,
                test_mode=test_mode)
    else:
        _run_op('uxm_relock',
                concurrent=concurrent,
                settling_time=settling_time)


def bias_dets(rfrac=None, concurrent=True, settling_time=0):
    """Bias the detectors on all SMuRF Controllers.

    Args:
        rfrac (float, tuple, optional): Target rfrac to aim for. If a float
            is provided, bias voltages will be chosen such that the median
            rfrac of each bias group is as close as possible to this value. If
            a tuple is provided, bias voltages will be chosen to maximize the
            number of channels within the given range. If None, the agent
            defaults are used. Defaults to None.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('bias_dets',
            concurrent=concurrent,
            settling_time=settling_time,
            rfrac=rfrac)


def set_biases(bias, bias_group=None, concurrent=True, settling_time=0):
    """Set the detector biases on all SMuRF Controllers.

    Args:
        bias: (int, float, list)
            Biases to set. If a float is passed, this will be used for all
            specified bias groups. If a list of floats is passed, it must be
            the same size of the list of bias groups.
        bias_group: (int, list, optional)
            Bias group or list of bias groups to set. If None, will set all
            bias groups. Defaults to None.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controlls if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('set_biases',
            concurrent=concurrent,
            settling_time=settling_time,
            bias=bias,
            bgs=bias_group)


def zero_biases(bias_group=None, concurrent=True, settling_time=0):
    """Set the detector biases on all SMuRF Controllers.

    Args:
        bias_group: (int, list, optional)
            Bias group or list of bias groups to set. If None, will zero all
            bias groups. Defaults to None.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controlls if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('zero_biases',
            concurrent=concurrent,
            settling_time=settling_time,
            bgs=bias_group)


def take_bgmap(tag=None, concurrent=True, settling_time=0):
    """Take a bgmap on all SMuRF Controllers.

    Args:
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('take_bgmap',
            concurrent=concurrent,
            settling_time=settling_time,
            tag=tag)


def take_noise(tag=None, concurrent=True, settling_time=0):
    """Measure noise statistics from a short, 30 second, timestream.

    Args:
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation.
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('take_noise',
            concurrent=concurrent,
            settling_time=settling_time,
            tag=tag)


def shutdown(concurrent=True, settling_time=0):
    """Safely shutdown the SMuRFs.

    This turns off tones, flux-ramp voltage and amplifier biases on all SMuRF
    Controllers.

    Args:
        concurrent (bool, optional): A bool which determines how the operation
            is run across the active SMuRF controllers. It runs in parallel if
            True, and in series if False.
        settling_time (float, optional):
            Time in seconds to wait between operation runs across the active
            SMuRF controllers if *not* running concurrently. If running
            concurrently this is ignored. Defaults to 0 seconds.

    """
    _run_op('all_off',
            concurrent=concurrent,
            settling_time=settling_time)


def _wait_for_stream_start(smurf, timeout):
    """Wait for, at most, timeout seconds until the stream for the specified
    smurf client is enabled.

    Args:
        smurf (ocs.ocs_client.OCSClient): pysmurf-controller client.
        timeout (int): Timeout for the check in seconds.

    """
    for i in range(int(timeout)):
        resp = smurf.stream.status()
        stream_on = resp.session['data'].get('stream_on', True)
        if stream_on:
            return
        time.sleep(1)

    raise RuntimeError(f"Stream for {smurf} did not turn on within {timeout} seconds.")


def stream(state, tag=None, subtype=None, wait_for_stream=True, **kwargs):
    """Stream data on all SMuRF Controllers.

    Args:
        state (str): Streaming state, either 'on' or 'off'.
        tag (str, optional): Tag or comma-separated listed of tags to attach to
            the operation.
        subtype (str, optional): Operation subtype used to tag the stream.
        wait_for_stream (bool, optional): If True, block until the streams are
            all enabled. If False, check that the client call goes through, but
            do not wait. Defaults to True.
        **kwargs: Additional keyword arguments. Passed through to the SMuRF
            controller unmodified. See the `controller documentation
            <https://socs.readthedocs.io/en/main/agents/pysmurf-controller.html#socs.agents.pysmurf_controller.agent.PysmurfController.stream>`_.

    """
    clients_to_remove = []

    if state.lower() == 'on':
        for smurf in run.CLIENTS['smurf']:
            smurf.stream.start(subtype=subtype, tag=tag, kwargs=kwargs)

        for smurf in run.CLIENTS['smurf']:
            resp = smurf.stream.status()
            try:
                check_started(smurf, resp, timeout=60)
                if wait_for_stream:
                    _wait_for_stream_start(smurf, timeout=120)
            except RuntimeError as e:
                print(f"Failed to start stream on {smurf}, removing from targets list.")
                print(e)
                smurf.stream.stop()
                clients_to_remove.append(smurf)

    else:
        print('Stopping SMuRF streams.')
        for smurf in run.CLIENTS['smurf']:
            try:
                smurf.stream.stop()
            # Handles case where agent becomes unreachable
            except ControlClientError as e:
                print(f"Failed to stop stream on {smurf}, removing from targets list.")
                print(e)
                clients_to_remove.append(smurf)

        # Remove failed SMuRF clients
        for client in clients_to_remove:
            run.CLIENTS['smurf'].remove(client)
        clients_to_remove = []

        for smurf in run.CLIENTS['smurf']:
            print(f'Waiting for stream from {smurf.instance_id} to stop.')
            resp = smurf.stream.wait()
            try:
                check_response(smurf, resp)
            except RuntimeError as e:
                print(f"Failed to stop stream on {smurf}, removing from targets list.")
                print(e)
                clients_to_remove.append(smurf)

    # Remove failed SMuRF clients
    for client in clients_to_remove:
        run.CLIENTS['smurf'].remove(client)

    # Check if enough SMuRFs remain
    _check_smurf_threshold()
