import signal

from . import acu, hwp, seq, smurf, stimulator, wiregrid

from .commands import wait_until
from .util import create_clients

CLIENTS = None


def initialize(test_mode=False):
    """Initialize global clients list.

    Args:
        test_mode (bool): Operate in 'test mode'. Use this to find Agents that
            are meant to stand in for real agents while testing, i.e.
            SmurfFileEmulators instead of PysmurfControllers.
    """
    global CLIENTS
    CLIENTS = create_clients(test_mode=test_mode)


__all__ = ["acu",
           "hwp",
           "seq",
           "smurf",
           "stimulator",
           "wiregrid",
           "wait_until",
           "initialize"]


# Treat SIGTERM like SIGINT and raise an exception
def term_handler(sig, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, term_handler)


# Define the variable '__version__':
# This has the closest behavior to versioneer that I could find
# https://github.com/maresb/hatch-vcs-footgun-example
try:
    # If setuptools_scm is installed (e.g. in a development environment with
    # an editable install), then use it to determine the version dynamically.
    from setuptools_scm import get_version

    # This will fail with LookupError if the package is not installed in
    # editable mode or if Git is not installed.
    __version__ = get_version(root="..", relative_to=__file__, version_scheme="no-guess-dev")
except (ImportError, LookupError):
    # As a fallback, use the version that is hard-coded in the file.
    try:
        from sorunlib._version import __version__  # noqa: F401
    except ModuleNotFoundError:
        # The user is probably trying to run this without having installed
        # the package, so complain.
        raise RuntimeError(
            "sorunlib is not correctly installed. "
            "Please install it with pip."
        )
