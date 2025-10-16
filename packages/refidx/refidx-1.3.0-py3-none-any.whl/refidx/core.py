# Authors: Benjamin Vial
# This file is part of pytmod
# License: GPLv3
# See the documentation at bvial.info/pytmod


"""Get refractive index from a database


This module allows you to retrieve the refractive index of a material at a given
wavelength from the refractiveindex.info_ database. It is inspired by the
repository_ by cinek810.

.. _refractiveindex.info:
    https://refractiveindex.info/

.. _repository:
    https://github.com/cinek810/refractiveindex.info

The database contains a large set of refractive indices of various materials, and
is updated regularly. The database is stored in a .npz file, which is loaded
when the module is imported.

The module provides two classes: `Material` and `DataBase`. The
`Material` class represents a material in the database, and provides methods to
get the refractive index of the material. The `DataBase` class represents the
database itself and provides methods to search the database and retrieve a
`Material` instance.

The module also provides a few functions to help with the search and retrieval of
materials. For example, the `find` function allows you to search the database by
name or formula, and the `get` function allows you to retrieve a material by its
id.

"""

__all__ = ["DataBase", "NonlinearDataBase", "Material"]

import os
import pprint
import random
from collections import UserDict
from copy import deepcopy

import numpy as np

path = os.path.dirname(os.path.abspath(__file__))
_db = np.load(os.path.join(path, "database.npz"), allow_pickle=True)

materials_path = _db["materials_path"].tolist()
database = _db["database"].tolist()

_db_nl = np.load(os.path.join(path, "database_nonlinear.npz"), allow_pickle=True)
materials_path_nl = _db_nl["materials_path"].tolist()
database_nl = _db_nl["database"].tolist()


def formula(lamb, coeff, formula_number):
    """
    Return the refractive index using a given formula.

    Parameters
    ----------
    lamb : float or array of floats
        Wavelength.
    coeff : array of floats
        Coefficients of the formula.
    formula_number : int
        Number of the formula to use.

    Returns
    -------
    n : complex or complex array
        The refractive index.

    Notes
    -----
    The formulas are given in the refractiveindex.info database.
    """
    if formula_number == 1:
        epsi = 0
        for i in reversed(list(range(1, np.size(coeff), 2))):
            epsi += (coeff[i] * lamb**2) / (lamb**2 - coeff[i + 1] ** 2)
        epsi += coeff[0] + 1
        n = np.sqrt(epsi)
    elif formula_number == 2:
        epsi = 0
        for i in reversed(list(range(1, np.size(coeff), 2))):
            epsi += (coeff[i] * lamb**2) / (lamb**2 - coeff[i + 1])
        epsi += coeff[0] + 1
        n = np.sqrt(epsi)
    elif formula_number == 3:
        epsi = coeff[0]
        for i in range(1, np.size(coeff), 2):
            epsi += coeff[i] * lamb ** coeff[i + 1]
        n = np.sqrt(epsi)
    elif formula_number == 4:
        coeff_ = np.zeros(17)
        for i, val in enumerate(coeff):
            coeff_[i] = val
        coeff = coeff_
        epsi = coeff[0]
        epsi += coeff[1] * lamb ** coeff[2] / (lamb**2 - coeff[3] ** coeff[4])
        epsi += coeff[5] * lamb ** coeff[6] / (lamb**2 - coeff[7] ** coeff[8])
        epsi += coeff[9] * lamb ** coeff[10]
        epsi += coeff[11] * lamb ** coeff[12]
        epsi += coeff[13] * lamb ** coeff[14]
        epsi += coeff[15] * lamb ** coeff[16]
        n = np.sqrt(epsi)
    elif formula_number == 5:
        n = coeff[0]
        for i in reversed(list(range(1, np.size(coeff), 2))):
            n += coeff[i] * lamb ** coeff[i + 1]
    elif formula_number == 6:
        n = coeff[0] + 1
        for i in reversed(list(range(1, np.size(coeff), 2))):
            n += coeff[i] / (coeff[i + 1] - lamb ** (-2))
    elif formula_number == 7:
        n = coeff[0]
        n += coeff[1] / (lamb**2 - 0.028)
        n += coeff[2] / (lamb**2 - 0.028) ** 2
        for i in range(3, np.size(coeff)):
            n += coeff[i] * lamb ** (2 * (i - 2))
    elif formula_number == 8:
        A = coeff[0]
        A += coeff[1] * lamb**2 / (lamb**2 - coeff[2])
        A += coeff[3] * lamb**2
        n = ((1 + 2 * A) / (1 - A)) ** 0.5
    elif formula_number == 9:
        epsi = coeff[0]
        epsi += coeff[1] / (lamb**2 - coeff[2])
        epsi += coeff[3] * (lamb - coeff[4]) / ((lamb - coeff[4]) ** 2 * +coeff[5])
        n = np.sqrt(epsi)
    return n


def check_bounds(lamb, dataRange):
    """
    Check if the given wavelength(s) are within the given data range.

    Parameters
    ----------
    lamb : float or array of floats
        Wavelength(s).
    dataRange : list of two floats
        Data range.

    Returns
    -------
    bool
        True if the wavelength(s) are within the data range, False otherwise.
    """
    return np.min(lamb) >= dataRange[0] and np.max(lamb) <= dataRange[1]


def get(d, l):
    """
    Get a nested value from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary.
    l : list of str
        List of keys to access the value.

    Returns
    -------
    value
        The value associated with the last key in l.

    Examples
    --------
    >>> get({'a': {'b': 1}}, ['a', 'b'])
    1
    """
    if len(l) == 1:
        return d[l[0]]
    return get(d[l[0]], l[1:])


class Material:
    """Material class"""

    def __init__(self, id):
        """
        Initialize a Material object.

        Parameters
        ----------
        id : list of str
            The id of the material, e.g. ["main", "Au", "Johnson"].
        """
        self.id = id

    def __repr__(self):
        """
        Return a string representation of the Material object.

        Returns
        -------
        str
            A string representation of the Material object, e.g. "Material Ag Glass BK7".
        """
        return f"Material " + (" ").join(self.id)

    @property
    def name(self):
        """
        Get the name of the material.

        Returns
        -------
        str
            The name of the material, e.g. "Ag / Glass / BK7".
        """
        return (" / ").join([s.capitalize() for s in self.id])

    @property
    def data(self):
        """
        Get the data associated with the material.

        Returns
        -------
        dict
            The data associated with the material.
        """
        return get(database, self.id)

    @property
    def material_data(self):
        """
        Get the material data.

        Returns
        -------
        dict
            The material data.
        """
        return self.data["DATA"]

    @property
    def references(self):
        """
        Get the references associated with the material.

        Returns
        -------
        list
            A list of references associated with the material.
        """
        return self.data["REFERENCES"]

    @property
    def type(self):
        """
        Get the type of the material.

        Returns
        -------
        str
            The type of the material, e.g. "tabulated" or "formula 1".
        """
        return self.material_data["type"]

    @property
    def comments(self):
        """
        Get the comments associated with the material.

        Returns
        -------
        str or None
            The comments associated with the material, or None if no comments are available.
        """
        try:
            comments = self.data["COMMENTS"]
        except:
            comments = None
        return comments

    @property
    def info(self):
        """
        Get a dictionary with comments and references associated with the material.

        Returns
        -------
        dict
            A dictionary with comments and references associated with the material.
        """
        return dict(comments=self.comments, references=self.references)

    @property
    def wavelength_range(self):
        """
        Get the wavelength range of the material.

        Returns
        -------
        list
            The wavelength range of the material, given as [min, max].
        """
        wlrange = self.material_data["wavelength_range"]
        if wlrange is None:
            wavelengths = self.material_data["wavelengths"]
            return [min(wavelengths), max(wavelengths)]
        return wlrange

    def get_index(self, wavelength):
        """
        Get the complex refractive index.

        Parameters
        ----------
        wavelength : float or array of floats
            Wavelength(s) in microns.

        Returns
        -------
        complex or array of complex
            The refractive index(es).

        Raises
        ------
        ValueError
            If the wavelength is not within the material's data range.

        Notes
        -----
        The refractive index is interpolated from the data stored in the material
        database. The interpolation is done using the `np.interp` function.

        The material data is stored in a dictionary with the following keys:

        * "wavelengths" : list of floats
            The wavelength range of the material.
        * "index" : list of complex
            The refractive index data.
        * "coefficients" : list of floats
            The coefficients of the formula used to calculate the refractive index.
        * "type" : str
            The type of the material, e.g. "tabulated" or "formula 1".

        The type of the material determines the interpolation method used:

        * "tabulated" : The refractive index is interpolated from the data stored in
          the material database.
        * "formula 1" : The refractive index is calculated using the formula given
          by the coefficients in the material database.

        """
        wrange = self.wavelength_range
        wavelength = np.array(wavelength)
        if not check_bounds(wavelength, wrange):
            raise ValueError(
                f"No data for this material {self.id}. Wavelength must be between {wrange[0]} and {wrange[1]} microns.",
            )

        if self.type.split()[0] == "tabulated":
            # Interpolate the refractive index from the data stored in the material
            # database.
            matLambda = np.array(self.material_data["wavelengths"])
            matN = np.array(self.material_data["index"])
            return np.interp(wavelength, matLambda, matN).conj()

        else:
            # Calculate the refractive index using the formula given by the
            # coefficients in the material database.
            return formula(
                wavelength,
                self.material_data["coefficients"],
                int(self.type.split()[1]),
            )

    def print_info(self, html=False, tmp_dir=None, filename="out.html"):
        """
        Print the material information.

        The material information is a dictionary with the keys "comments",
        "references", and "type". The value associated with the "comments" key is
        the comments associated with the material, the value associated with the
        "references" key is a list of references associated with the material, and
        the value associated with the "type" key is the type of the material, e.g.
        "tabulated" or "formula 1".

        Parameters
        ----------
        html : bool
            If True, print the material information as HTML. If False, print as a
            plain text dictionary.
        tmp_dir : str
            If not None, save the HTML to a file in the given directory. If None,
            display the HTML using IPython.display.HTML if available, otherwise
            print the material information as a plain text dictionary.
        """
        if html:
            html_data = "".join(
                [
                    "<h5>" + k.title() + "</h5>" + "<p>" + v + "</p>"
                    for k, v in self.info.items()
                    if v is not None
                ]
            )
            html_data = "<div class=matdata>" + html_data + "</div>"

            if tmp_dir is not None:
                # building the docs with sphinx-gallery
                assert os.path.exists(tmp_dir)
                with open(os.path.join(tmp_dir, filename), "wt") as fh:
                    fh.write(html_data)
            else:
                try:
                    # running from a terminal or jupyter
                    from IPython.display import HTML, display

                    display(HTML(html_data))
                except ImportError:
                    print(self.info)
        else:
            print(self.info)


def recursive_items(dictionary, dtype=dict):
    """
    Generator that yields all items in a nested dictionary.

    Parameters
    ----------
    dictionary : dict
        The dictionary to iterate over.
    dtype : type, optional
        The type of the values to yield. If not given, defaults to dict.

    Yields
    ------
    item : tuple
        A tuple containing the key, value, and parent dictionary.
    """
    for key, value in dictionary.items():
        if isinstance(value, dtype):  # check if value is of type dtype
            yield (key, value, dictionary)
            # if value is of type dtype, recursively call the function
            yield from recursive_items(value, dtype)
        else:
            # if value is not of type dtype, yield the item
            yield (key, value, dictionary)


class MaterialDict(UserDict):
    """
    A dictionary of materials.

    Parameters
    ----------
    material_dict : dict
        The dictionary to use as the underlying data structure.

    Notes
    -----
    The dictionary is a nested dictionary, where each key is a string and each
    value is either a `Material` instance or another `MaterialDict`
    instance.
    """

    def __init__(self, material_dict):
        super().__init__(material_dict)

    def print(self):
        """
        Print the dictionary.

        Notes
        -----
        This will print the dictionary in a human-readable format.
        """
        pprint.pprint(self)

    def list(self):
        """
        Get a list of all keys in the dictionary.

        Returns
        -------
        list
            A list of all keys in the dictionary.
        """
        return list(self.keys())

    def findkeys(self, strtofind):
        """
        Find all keys that contain a given string.

        Parameters
        ----------
        strtofind : str
            The string to search for.

        Returns
        -------
        keys : list of str
            The keys that contain the given string.
        """
        return [*_find_paths(self, strtofind)]

    def find(self, strtofind):
        """
        Find all materials that have a given string in their id.

        Parameters
        ----------
        strtofind : str
            The string to search for.

        Returns
        -------
        materials : list of Material
            The materials that have the given string in their id.
        """
        return [_nested_get(self, p) for p in [*self.findkeys(strtofind)]]


def _find_paths(nested_dict, value, prepath=()):
    """
    Generator that yields all paths to a given value in a nested dictionary.

    Parameters
    ----------
    nested_dict : dict
        The nested dictionary to search in.
    value : any
        The value to search for.
    prepath : tuple, optional
        The path to the current dictionary, used to build the path to the found value.
        Default is an empty tuple.

    Yields
    ------
    path : tuple
        The path to the found value.

    Notes
    -----
    The path is a tuple of keys that leads to the found value. For example, if the
    value is found in a nested dictionary with the structure::

        {a: {b: {c: value}}}

    The path will be `('a', 'b', 'c')`.

    """
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if k == value:  # found value
            yield path
        elif hasattr(v, "items"):  # v is a dict
            yield from _find_paths(v, value, path)


def _nested_get(dic, keys):
    """
    Get a nested value from a dictionary.

    Parameters
    ----------
    dic : dict
        The dictionary to get the value from.
    keys : list of str
        The list of keys to access the value.

    Returns
    -------
    value
        The value associated with the last key in `keys`.

    Notes
    -----
    This function is a simple implementation of the `dict.get` method.
    """
    for key in keys:
        dic = dic[key]
    return dic


def _transform(d):
    """
    Recursively transform a nested dictionary by replacing all sub-dictionaries
    with MaterialDict instances.

    Parameters
    ----------
    d : dict
        The dictionary to transform.

    Returns
    -------
    dict
        The transformed dictionary.
    """
    # Iterate over the items in the dictionary
    for k, v in d.items():
        # If the value is a dictionary, and not a Material instance
        if hasattr(v, "items") and not isinstance(v, Material):
            # Replace the value with a MaterialDict instance
            v = MaterialDict(v)
            # Recursively transform the MaterialDict instance
            d[k] = _transform(v)
        else:
            # Otherwise, leave the value unchanged
            d[k] = v
    # Return the transformed dictionary
    return d


def process_database(database, materials_path):

    # Copy the database to avoid modifying the original database
    database_mat = deepcopy(database)
    # database_mat = database

    # Iterate over the database and replace each material dictionary with a
    # Material instance
    nb_mat = 0
    for key, value, dictionary in recursive_items(database_mat):
        if type(value) is dict and "DATA" in value.keys():
            # Create a Material instance using the path to the material file
            dictionary[key] = Material(materials_path[nb_mat].split("/"))
            # Increment the material number
            nb_mat += 1

    # Transform the database to replace all sub-dictionaries with MaterialDict
    # instances
    database_mat = MaterialDict(database_mat)
    database_mat = _transform(database_mat)
    return database_mat, nb_mat


database_mat, nb_mat = process_database(database, materials_path)
database_mat_nl, nb_mat_nl = process_database(database, materials_path)


def nested_dict_keys_list(nested_dict):
    """Get all the keys of a nested dictionary as a list of lists of keys."""
    keys = []
    for key, value in nested_dict.items():
        if isinstance(value, MaterialDict):
            for k in nested_dict_keys_list(value):
                keys.append([key] + k)
        else:
            keys.append([key])
    return keys


class _DataBase:
    """
    Material database

    This class provides access to the refractiveindex.info material database.
    """

    def __init__(self, database_mat):
        """
        Initialize the database

        The database is stored in a nested dictionary, which is a instance of
        the MaterialDict class.
        """
        self._materials = database_mat

    @property
    def materials(self):
        return self._materials

    @property
    def keys_list(self):
        """Read-only list of all material keys."""
        return nested_dict_keys_list(self.materials)

    def random(self):
        """
        Get a random material from the database.

        This method will return a random material from the database. The
        material is selected by randomly selecting a key from the nested
        dictionary until a Material instance is found.
        """
        mat = self.materials
        while isinstance(mat, MaterialDict):
            mat = random.choice(list(mat.values()))
        return mat

    def get_item(self, keys):
        """Get an item from a nested dictionary given a list of keys."""
        item = self.materials
        for key in keys:
            item = item[key]
        return item


class DataBase(_DataBase):
    """
    Material database

    This class provides access to the refractiveindex.info material database.
    """

    def __init__(self):
        super().__init__(database_mat)


class NonlinearDataBase(_DataBase):
    """
    Nonlinear material database

    This class provides access to the refractiveindex.info nonlinear material database.
    """

    def __init__(self):
        super().__init__(database_mat_nl)
