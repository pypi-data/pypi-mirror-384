# Authors: Benjamin Vial
# This file is part of pytmod
# License: GPLv3
# See the documentation at bvial.info/pytmod


def test_nometadata():
    import importlib

    import refidx

    importlib.reload(refidx.__about__)


def test_data():
    import refidx

    refidx.__about__.get_meta(None)
