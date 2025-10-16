# Authors: Benjamin Vial
# This file is part of pytmod
# License: GPLv3
# See the documentation at bvial.info/pytmod

import pytest


def _test_material(mat):
    """
    Test a material.

    This function tests a material by:
    - printing its name and info
    - getting its refractive index at a specific wavelength
    - checking that it raises a ValueError when the wavelength is out of range

    Parameters
    ----------
    mat : refidx.Material
        The material to test.

    """

    ## Print the material's name, info and wavelength range
    print(mat)
    print(mat.name)
    # print(mat.data)  # uncomment this to see the raw data
    print(mat.info)

    wr = mat.wavelength_range
    if wr is not None:
        # Get the wavelength in the middle of the range
        lamb = (wr[1] + wr[0]) / 2
    else:
        # If the material has no wavelength range, use 1.0 as a default
        lamb = 1.0

    # Get the refractive index at the chosen wavelength
    index = mat.get_index(lamb)
    print("wavelength range: ", mat.wavelength_range)
    print("wavelength", lamb)
    print("refractive index: ", index)

    # Check that the material raises a ValueError when the wavelength is out of range
    if wr is not None:
        with pytest.raises(ValueError):
            # Try to get the refractive index at a wavelength below the range
            lamb = mat.wavelength_range[0] / 2
            index = mat.get_index(lamb)

        with pytest.raises(ValueError):
            # Try to get the refractive index at a wavelength above the range
            lamb = mat.wavelength_range[1] * 2
            index = mat.get_index(lamb)


def test_all():
    import os

    import refidx

    databases = [refidx.DataBase(), refidx.NonlinearDataBase()]

    for database in databases:

        print(database.keys_list)

        materials = database.materials
        print(materials.print())
        print(materials.list())
        print(materials.findkeys(["Si", "Au"]))
        print(materials.find("Ag"))

        database.get_item(["main", "Au", "Johnson"])
        j = 0
        for key, value, dictionary in refidx.core.recursive_items(
            materials, refidx.core.MaterialDict
        ):

            if isinstance(value, refidx.Material):
                print("######################################################")
                _test_material(value)
                j += 1

        assert j == refidx.core.nb_mat
        mat = database.random()
        assert isinstance(mat, refidx.Material)

        mat.print_info()
        mat.print_info(True)
        mat.print_info(True, ".")
        os.remove("out.html")


def test_print_ipython(monkeypatch):
    import importlib
    import sys

    monkeypatch.setitem(sys.modules, "IPython.display", None)
    import refidx

    importlib.reload(refidx)
    database = refidx.DataBase()
    mat = database.random()
    mat.print_info(True)
