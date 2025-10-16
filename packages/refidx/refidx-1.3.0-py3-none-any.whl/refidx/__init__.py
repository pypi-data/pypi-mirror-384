# Authors: Benjamin Vial
# This file is part of pytmod
# License: GPLv3
# See the documentation at bvial.info/pytmod

"""
Top-level package for refidx.

The main classes and functions are:

- `Material`: A class representing a refractive index material.
- `DataBase`: A class representing the refractive index database.
- `MaterialDict`: A dictionary of materials.
- `find`: A function to search the database by name or formula.
- `get`: A function to retrieve a material by its id.
"""

from .__about__ import __author__, __description__, __version__
from .core import *
