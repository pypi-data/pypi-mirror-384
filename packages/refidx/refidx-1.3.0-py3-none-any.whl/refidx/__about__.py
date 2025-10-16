# Authors: Benjamin Vial
# This file is part of pytmod
# License: GPLv3
# See the documentation at bvial.info/pytmod

"""
Get metadata from the package
"""

import importlib.metadata as metadata


def get_meta(metadata):
    """
    Get metadata from the package.

    Parameters
    ----------
    metadata : module
        The module to use to get the metadata.

    Returns
    -------
    version : str
        The version of the package.
    author : str
        The author of the package.
    description : str
        A short description of the package.
    """
    try:
        data = metadata.metadata("refidx")
        __version__ = metadata.version("refidx")
        __author__ = data.get("author")
        __description__ = data.get("summary")
    except Exception:
        __version__ = "unknown"
        __author__ = "unknown"
        __description__ = "unknown"
    return __version__, __author__, __description__


__version__, __author__, __description__ = get_meta(metadata)
