import os
import re

from sorunlib.config import load_config

from ocs import site_config
from ocs.ocs_client import OCSClient
from ocs.client_http import ControlClientError


class CrossbarConnectionError(Exception):
    pass


def _load_site_config(filename=None):
    """Load a site config file, searching for default.yaml in OCS_CONFIG DIR by
    default.

    Args:
        filename (str): Path to OCS site config file

    Returns:
        ocs.site_config.SiteConfig object

    """
    if filename is None:
        assert (os.getenv('OCS_CONFIG_DIR') is not None)
        site = 'default'
        filename = os.path.join(os.getenv('OCS_CONFIG_DIR'),
                                site + '.yaml')
    cfg = site_config.SiteConfig.from_yaml(filename)

    return cfg


def _find_instances(agent_class, host=None, config=None):
    """Find all instances of an Agent Class in a config.

    Args:
        agent_class (str): Agent Class name to search for, must match Agent
            Class defined by an OCS Agent (and thus also defined in the SCF.)
        host (str): Specific host to search on, if None all hosts will be
            searched.
        config (str): Path to the OCS Site Config File. If None the default
            file in OCS_CONFIG_DIR will be used.

    Returns:
        list: List of instance-id's matching the given agent_class.

    """
    cfg = _load_site_config(config)

    if host is not None:
        hosts = {host: cfg.hosts[host]}
    else:
        hosts = cfg.hosts

    instances = []
    for _host, hostcfg in hosts.items():
        for entry in hostcfg.instances:
            if entry['agent-class'] == agent_class:
                instances.append(entry['instance-id'])

    return instances


def _find_active_instances(agent_class):
    """Find all instances of an Agent Class currently online, based on the
    Agents known by the registry.

    Args:
        agent_class (str): Agent Class name to search for, must match Agent
            Class defined by an OCS Agent (and thus also defined in the SCF.)

    Returns:
        str or list: List of instance-id's matching the given agent_class. If
            the list is of length 1, just return the only instance-id.

    """
    cfg = load_config()

    reg_client = _try_client(cfg['registry'])
    _, _, session = reg_client.main.status()

    instances = []
    for entry in session['data'].values():
        if entry['expired']:
            continue

        if entry['agent_class'] == agent_class:
            instance_id = entry['agent_address'].split('.')[-1]
            instances.append(instance_id)

    if len(instances) == 1:
        return instances[0]

    return instances


def _try_client(instanceid):
    """User in place of OCSClient to handle common exceptions."""
    if not instanceid:
        return

    try:
        client = OCSClient(instanceid)
    except ControlClientError as e:
        # crossbar connection error
        if "Failed to connect" in str(e):
            result = re.search(r"(http://[^ ]+)'", str(e))
            crossbar_url = result.group(1)
            error = f"Cannot connect to crossbar server {crossbar_url}. Check your connection."
            raise CrossbarConnectionError(error)
        # likely an agent connection error
        if "no callee registered" in str(e):
            print(f"Could not instantiate OCSClient for '{instanceid}'.")
            return None
        # other errors, i.e. non-200 error codes
        print(f"Unexpected error trying to instantiate OCSClient for '{instanceid}'.")
        raise ControlClientError(e)

    return client


def _create_wiregrid_clients(config=None, sorunlib_config=None):
    """Create all wiregrid related clients for a single platform.

    Args:
        config (str): Path to the OCS Site Config File. If None the default
            file in OCS_CONFIG_DIR will be used.
        sorunlib_config (str): Path to sorunlib config file. If None the path
            from environment variable SORUNLIB_CONFIG is used.

    Returns:
        dict: Dictionary with the keys, 'acutator', 'encoder', 'kikusui', and
            'labjack' with each value being the corresponding OCSClient.

    """
    actuator = _find_active_instances('WiregridActuatorAgent')
    encoder = _find_active_instances('WiregridEncoderAgent')
    kikusui = _find_active_instances('WiregridKikusuiAgent')

    cfg = load_config(filename=sorunlib_config)
    try:
        labjack = cfg['wiregrid']['labjack']
    except KeyError:
        labjack = None

    clients = {'actuator': _try_client(actuator),
               'encoder': _try_client(encoder),
               'kikusui': _try_client(kikusui),
               'labjack': _try_client(labjack)}

    return clients


def _create_stimulator_clients():
    """Create all stimulator related clients.

    Returns:
        dict: Dictionary with the keys, 'blh', 'pcr500ma', and 'ds378'
            with each value being the corresponding OCSClient.

    """
    blh_id = _find_active_instances('BLHAgent')
    pcr500ma_id = _find_active_instances('PCR500MAAgent')
    ds378_id = _find_active_instances('DS378Agent')

    clients = {}

    if blh_id:
        clients['blh'] = _try_client(blh_id)

    if pcr500ma_id:
        clients['pcr500ma'] = _try_client(pcr500ma_id)

    if ds378_id:
        clients['ds378'] = _try_client(ds378_id)

    return clients


def create_clients(config=None, sorunlib_config=None, test_mode=False):
    """Create all clients needed for commanding a single platform.

    Args:
        config (str): Path to the OCS Site Config File. If None the default
            file in OCS_CONFIG_DIR will be used.
        sorunlib_config (str): Path to sorunlib config file. If None the path
            from environment variable SORUNLIB_CONFIG is used.
        test_mode (bool): Operate in 'test mode'. Use this to find Agents that
            are meant to stand in for real agents while testing, i.e.
            SmurfFileEmulators instead of PysmurfControllers.

    Returns:
        dict: Dictionary with the ACU and SMuRF clients needed for commanding
        in the format::

            clients = {'acu': acu_client,
                       'hwp': hwp_supervisor_client,
                       'smurf': [smurf_client1, smurf_client2, smurf_client3],
                       'wiregrid': {'actuator': actuator_client,
                                    'encoder': encoder_client,
                                    'kikusui': kikusui_client,
                                    'labjack': labjack_client}}

    """
    clients = {}

    if test_mode:
        smurf_agent_class = 'SmurfFileEmulator'
    else:
        smurf_agent_class = 'PysmurfController'

    acu_id = _find_active_instances('ACUAgent')
    hwp_id = _find_active_instances('HWPSupervisor')
    smurf_ids = _find_active_instances(smurf_agent_class)

    if acu_id:
        acu_client = _try_client(acu_id)
        clients['acu'] = acu_client
    if hwp_id:
        hwp_client = _try_client(hwp_id)
        clients['hwp'] = hwp_client

    if isinstance(smurf_ids, str):
        # when only a single SMuRF controller online
        smurf_clients = [smurf_ids]
    else:
        # create smurf client list, even if empty
        smurf_clients = [_try_client(x) for x in smurf_ids]
    clients['smurf'] = smurf_clients

    clients['wiregrid'] = _create_wiregrid_clients(
        config=config,
        sorunlib_config=sorunlib_config)

    clients['stimulator'] = _create_stimulator_clients()

    return clients
