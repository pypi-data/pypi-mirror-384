"""Internal module for shared utilities within sorunlib.

The usual caveats apply, these interfaces might change without notice.

"""

import datetime as dt
import signal
import time

from functools import wraps

import ocs
import sorunlib as run

from sorunlib.commands import _timestamp_to_utc_datetime


def _check_error(client, response):
    """Check if a response is an error or timeout."""
    op = response.session['op_name']
    instance = client.instance_id

    if response.status == ocs.ERROR:
        error = f"Request for Operation {op} in Agent {instance} failed.\n" + \
            str(response)
        raise RuntimeError(error)
    elif response.status == ocs.TIMEOUT:
        error = f"Timeout reached waiting for {op} in Agent {instance} to " + \
            "complete.\n" + str(response)
        raise RuntimeError(error)


def check_response(client, response):
    """Check that a response from OCS indicates successful task/process
    completion.

    Args:
        client (ocs.ocs_client.OCSClient): OCS Client which returned the
            response.
        response (ocs.ocs_client.OCSReply): Response from an OCS operation
            call.

    Raises:
        RuntimeError: When Operation has not completed successfully (either on
            initial request or after completion) or the response has timed out.

    """
    try:
        op = response.session['op_name']
    except KeyError:
        error = f"Unable to parse response from {client}:\n{str(response)}"
        raise RuntimeError(error)
    instance = client.instance_id

    _check_error(client, response)

    if not response.session['success']:
        error = f'Task {op} in Agent {instance} failed to complete " + \
            "successfully.\n' + str(response)
        raise RuntimeError(error)


def check_running(client, response):
    """Check that a response from OCS indicates a task/process is still
    running.

    Args:
        client (ocs.ocs_client.OCSClient): OCS Client which returned the
            response.
        response (ocs.ocs_client.OCSReply): Response from an OCS operation
            call.

    Raises:
        RuntimeError: When Operation is not running.

    """
    op = response.session['op_name']
    instance = client.instance_id

    _check_error(client, response)
    if response.session['status'] != 'running':
        error = f"Operation {op} in Agent {instance} is not in the 'running' " + \
            "state.\n" + str(response)
        raise RuntimeError(error)


def check_started(client, response, timeout=60):
    """Check that a process has started and is in the 'running' state. If it
    has not finished starting, wait for timeout seconds for it to start. If
    it is not running by then, raise exception.

    This is meant to be called right after a process' start call is made, to
    ensure that process starts successfully. Use ``check_running()`` if you
    want to check that an already running process is still running.

    Args:
        client (ocs.ocs_client.OCSClient): OCS Client which returned the
            response.
        response (ocs.ocs_client.OCSReply): Response from an OCS operation
            call.
        timeout (float): How long to wait, in seconds, for the operation to go
            from 'starting' to 'running' before raising an exception.

    Raises:
        RuntimeError: When Operation does not properly transition from
            'starting' to 'running' or is not 'running'.

    """
    op = response.session['op_name']
    instance = client.instance_id

    _check_error(client, response)

    op_code = response.session.get('op_code')

    if op_code == 2:  # STARTING
        _operation = client.__getattribute__(op)

        # Wait at most ~timeout seconds while checking the status
        for i in range(timeout):
            response = _operation.status()
            _check_error(client, response)
            op_code = response.session.get('op_code')
            if op_code == 3:  # RUNNING
                # Tricky to change state during testing w/little reward
                return  # pragma: no cover
            time.sleep(1)

        print("The operation is in an unexpected state after {timeout} seconds.")

    if op_code != 3:  # RUNNING
        error = f"Operation {op} in Agent {instance} is not 'running'.\n" + \
            f"Current OpCode: {op_code}\n" + str(response)
        raise RuntimeError(error)


def _check_operation_running(client, operation):
    op = client.__getattribute__(operation)
    resp = op.status()
    check_running(client, resp)


def _seconds_until_target(target):
    target_dt = _timestamp_to_utc_datetime(target)
    now = dt.datetime.now(dt.timezone.utc)
    diff = (target_dt - now).total_seconds()
    return max(diff, 0)


def monitor_process(client, operation, stop_time, check_interval=10):
    """Monitor a running process.

    This will block until ``stop_time``, checking that the process given in
    ``operation`` is still running every ``check_interval`` seconds.

    Args:
        client (ocs.ocs_client.OCSClient): OCS Client that has the process to
            monitor.
        operation (str): Operation name to monitor.
        stop_time (str): Time in ISO format and in UTC timezone to stop
            monitoring the process. If UTC ("+00:00") is not explicitly used in
            the timestamp it is assumed.
        check_interval (float): Interval, in seconds, at which the Operation
            status is checked. Defaults to 10 seconds.

    Raises:
        RuntimeError: If Operation stops running before ``stop_time``.

    """
    diff = _seconds_until_target(stop_time)

    while diff > 0:
        # Check process response
        _check_operation_running(client, operation)

        # Wait until next check
        if diff > check_interval:
            time.sleep(check_interval)
        else:
            # Recompute diff to avoid waiting too long
            diff = _seconds_until_target(stop_time)
            time.sleep(diff)

        # Recompute diff
        diff = _seconds_until_target(stop_time)


def protect_shutdown(f):
    """Decorator to install temporary signal handlers while operations required
    to safely shutdown are handled.

    This will catch and print the caught signals to ``stdout`` while shutdown
    is happening. Currently handles only ``SIGINT`` and ``SIGTERM``.

    """
    @wraps(f)
    def wrapper(*args, **kwds):
        def handler(sig, frame):
            print(f'Caught {signal.Signals(sig).name} during shutdown.')

        int_handler = signal.signal(signal.SIGINT, handler)
        term_handler = signal.signal(signal.SIGTERM, handler)

        result = f(*args, **kwds)

        signal.signal(signal.SIGINT, int_handler)
        signal.signal(signal.SIGTERM, term_handler)
        return result
    return wrapper


@protect_shutdown
def stop_smurfs():
    """Simple wrapper to shutdown all SMuRF systems and handle any errors that
    occur.

    """
    try:
        run.smurf.stream('off')
    except RuntimeError as e:
        print(f"Caught error while shutting down SMuRF streams: {e}")
