import os
import yaml


def load_config(filename=None):
    """Load sorunlib config file, using SORUNLIB_CONFIG by default.

    Args:
        filename (str): Path to sorunlib config file

    Returns:
        dict

    """
    if filename is None:
        assert (os.getenv('SORUNLIB_CONFIG') is not None)
        filename = os.getenv('SORUNLIB_CONFIG')

    with open(filename, 'rb') as f:
        return yaml.safe_load(f)
