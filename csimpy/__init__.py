from ._version import __version__

from .core import exec_sedml_docs_in_combine_archive  # noqa: F401

__all__ = [
    '__version__',
    'get_simulator_version',
    'exec_sedml_docs_in_combine_archive',
]

def get_simulator_version():
    """ Get the version of CSimPy

    Returns:
        :obj:`str`: version of CSimPy
    """
    return __version__