"""Module to build thermodynamic properties of species."""

import numpy as np
from scipy.interpolate import interp1d
from ms_thermo.constants import GAS_CST, ATOMIC_WEIGHTS

__all__ = [
    "build_thermo_from_avbp",
    "build_thermo_from_cantera",
    "build_thermo_from_chemkin",
]


class _NasaPolys:
    r"""
    Container class building NASA 7-coeffs polynomials \
    to build functions evaluating species thermodynamic properties per \
    mass unit. mass enthalpy of species k for instance is computed as : \

    .. math:: \frac{R}{W_k} (a_{5,k} + sum{i=0}^4 \frac{a_{i,k}}{i+1}T^{i+1})
    """

    def __init__(self, coeffs, t_range, molecular_weight):
        """Instanciation  of _NasaPolys

        Parameters :
        ==========
        coeffs : a dictionary of NASA 7 polynomials corresponding
                 to "low" and "high" temperature ranges
        t_range : a dictionary of three entries: min, mid and max
                  separating temperature low range ([T_min, T_mid]) and
                  high range ([T_mid, T_max])
        molecular_weight : species molecular weight
        """

        self.enthalpy_polys = dict()
        self.enthalpy_polys["high"] = None
        self.enthalpy_polys["low"] = None
        self.t_range = t_range
        self.molecular_weight = molecular_weight
        for k in ["high", "low"]:
            # Build enthalpy polynomials
            # ie. h_k(T) = a_5 + \sum_{i=0}^4 a_{i,k}/(i+1)T^{i+1}
            poly = np.zeros(6)
            poly[0] = coeffs[k][5]
            for i in range(5):
                poly[i + 1] = coeffs[k][i] / (i + 1)
            # transform polynomial coeffs to mass and SI unit(J/kg)
            poly *= GAS_CST / molecular_weight
            self.enthalpy_polys[k] = np.polynomial.polynomial.Polynomial(poly)

    def get_total_enthalpy(self, temp):
        r"""Computing species total enthalpy as :
        $\frac{R}{W_k} (a_{5,k} + sum{i=0}^4 \frac{a_{i,k}}{i+1}T^{i+1})$
        depending on the range of temperature i.e: "low" range polynomial
        is used if temperature is lower than T_mid, and "high" range is
        used otherwise

        Parameters :
        ==========
        temp : a temperature array for which enthalpy is evaluated

        Returns :
        =======
        enthalpy : species total enthalpy array
        """
        _temp = np.float64(temp)
        condlist = [
            _temp < self.t_range["mid"],
            np.logical_and(_temp >= self.t_range["mid"], _temp <= self.t_range["max"]),
        ]
        funclist = [self.enthalpy_polys["low"], self.enthalpy_polys["high"]]
        enthalpy = np.piecewise(_temp, condlist, funclist)
        enthalpy -= self.enthalpy_polys["low"](0)
        return enthalpy

    def get_total_energy(self, temp):
        r"""Computing total mass energy as : $e_k(T) = h_k(T) -RT=W_k$

        Parameters :
        ==========
        temp : a temperature array for which energy is evaluated

        Returns :
        =======
        energy : species total energy array
        """

        enthalpy = self.get_total_enthalpy(temp)
        energy = enthalpy - GAS_CST * temp / self.molecular_weight
        return energy


def _get_mol_weight_from_elements(elements):
    r"""Computes species molecular weight given atomic composition as :
    $W_k = \sum_{i=1}^N_{el} b_{i,k} w_i$

    Parameters :
    ==========
    element : a dictionary mapping species elements names to their numbers

    Returns :
    =======
    molecular_weight : species molecular weight
    """
    molecular_weight = 0.0
    for k in elements:
        molecular_weight += ATOMIC_WEIGHTS[k.lower()] * elements[k]
    return molecular_weight


def _get_species_indexes(database_file, db_format):
    """Get indexes of species entries in a thermo database file

    Parameters :
    ==========
    database_file : full path to database file
    db_format : the database format, possible values :
                - cantera / - chemkin / -avbp
    Returns :
    =======
    db_stream : the stream (content) of the database file
    indexes : list of species line indexes in the database file
    """
    with open(database_file, "r") as fin:
        db_stream = fin.readlines()

    indexes = []

    for i, line in enumerate(db_stream, 0):
        line = line.strip()
        cond = any(
            [
                (db_format == "avbp") and (line.startswith("species_name =")),
                (db_format == "chemkin") and (line.endswith(" 1")),
                (db_format == "cantera") and (line.startswith("species(")),
            ]
        )
        if cond:
            indexes.append(i)
    return db_stream, indexes


def _make_props_avbp(species_description):
    """Get species properties from AVBP like thermo database

    Parameters :
    ==========
    species_description : a list of strings containing species information

    Returns :
    =======
    props : a dictionary holding species properties. It contains the keys:
            - species_name : species name
            - molecular_weight : species molecular weight
            - total_energy : a temperature function returning species
                                total energy
            - total_enthalpy : a temperature function returning species
                                total enthalpy
    """

    def _avbp_str_to_float(str_val):
        """
        *Convert the given string to a float.*

        :param str_val: A string type value
        :returns: A float type value
        """
        number = str_val
        for sub in ["d", "D"]:
            number = number.replace(sub, "e")
        number = float(number)
        return number

    props = dict()
    props["species_name"] = [
        line.split()[-1]
        for line in species_description
        if line.startswith("species_name =")
    ][0]

    props["atoms"] = dict()

    for line in species_description:
        if line.startswith("species_molecular_weight ="):
            number = line.strip().split("=")[-1]
            props["molecular_weight"] = _avbp_str_to_float(number)

        if line.startswith("species_C_atoms"):
            number = line.strip().split("=")[-1]
            props["atoms"]["C"] = _avbp_str_to_float(number)
        if line.startswith("species_H_atoms"):
            number = line.strip().split("=")[-1]
            props["atoms"]["H"] = _avbp_str_to_float(number)
        if line.startswith("species_O_atoms"):
            number = line.strip().split("=")[-1]
            props["atoms"]["O"] = _avbp_str_to_float(number)
        if line.startswith("species_N_atoms"):
            number = line.strip().split("=")[-1]
            props["atoms"]["N"] = _avbp_str_to_float(number)

        if line.startswith("species_enthalpy_table ="):
            # Reading and computing table of molar sensible enthalpy
            # i.e : $h_s = int_{T_0}^{T} C_{p,k}^m dT$
            # given for the temperature range [0, 5000] whose step is 100K
            number = line.strip().split("=")[-1]

            number = np.array([_avbp_str_to_float(k) for k in number.split() if k])
            number -= number[0]

            t_range = np.linspace(0.0, 5000.0, 51)
            total_energy_tbl = np.zeros_like(t_range)
            total_enth_tbl = np.zeros_like(t_range)

            if len(t_range) == len(number):
                # in AVBP, the energy noted E is the total non chemical energy
                # i.e. not including the formation enthalpy
                total_enth_tbl = number
                # Computing the molar total energy
                # i.e $e_k^m = h_s - RT $
                total_energy_tbl = total_enth_tbl - GAS_CST * t_range

    # Building the function returning the total MASS energy and enthalpy
    # given the temperature
    if props["molecular_weight"] > 0:
        total_energy_tbl /= props["molecular_weight"]
        total_enth_tbl /= props["molecular_weight"]

    props["total_energy"] = interp1d(t_range, total_energy_tbl, kind="linear")
    props["total_enthalpy"] = interp1d(t_range, total_enth_tbl, kind="linear")
    return props


def _make_props_chemkin(species_description):
    """Get species properties from Chemkin like thermo database

    Parameters :
    ==========
    species_description : a list of strings containing species information

    Returns :
    =======
    props : a dictionary holding species properties. It contains the keys:
            - species_name : species name
            - molecular_weight : species molecular weight
            - total_energy : a temperature function returning species
                                total energy
            - total_enthalpy : a temperature function returning species
                                total enthalpy
    """
    props = dict()
    props["species_name"] = species_description[0][0:18].strip()

    line = species_description[0].strip()
    t_range = dict()
    elements = dict()
    coeffs = dict()

    coeffs["high"] = np.zeros(7)
    coeffs["low"] = np.zeros(7)

    t_range["min"] = float(line[45:55])
    t_range["max"] = float(line[55:65])
    t_range["mid"] = float(line[65:73])

    for i in range(4):
        elem_list = line[24 + i * 5 : 29 + i * 5].strip().split()
        if elem_list:
            elements[elem_list[0]] = int(elem_list[1])

    line = species_description[1].split("\n")[0]
    for i in range(5):
        coeffs["high"][i] = float(line[i * 15 : (i + 1) * 15])

    line = species_description[2].split("\n")[0]
    for i in range(2):
        coeffs["high"][i + 5] = float(line[i * 15 : (i + 1) * 15])
    for i in range(2, 5):
        coeffs["low"][i - 2] = float(line[i * 15 : (i + 1) * 15])

    line = species_description[3].split("\n")[0]
    for i in range(4):
        coeffs["low"][i + 3] = float(line[i * 15 : (i + 1) * 15])

    # computing molecular weight
    props["molecular_weight"] = _get_mol_weight_from_elements(elements)

    nasa = _NasaPolys(coeffs, t_range, props["molecular_weight"])
    props["total_energy"] = nasa.get_total_energy
    props["total_enthalpy"] = nasa.get_total_enthalpy
    props["atoms"] = elements
    return props


def _make_props_cantera(species_description):
    """Get species properties from Cantera like thermo database

    Parameters :
    ==========
    species_description : a list of strings containing species information

    Returns :
    =======
    props : a dictionary holding species properties. It contains the keys:
            - species_name : species name
            - molecular_weight : species molecular weight
            - total_energy : a temperature function returning species
                                total energy
            - total_enthalpy : a temperature function returning species
                                total enthalpy
    """
    props = dict()
    props["species_name"] = [
        line for line in species_description if line.startswith("species(name")
    ][0].strip()
    for sub in ['"', "'", ",", "species(name", "="]:
        props["species_name"] = props["species_name"].replace(sub, "")

    elements = dict()
    t_range = dict()
    coeffs = dict()

    line = ""
    for line in species_description:
        if all([k in line for k in ("=", ":", ",", "atoms")]):
            break
    line = " ".join(line.split())
    for k in ("=", ",", "atoms", "'", '"'):
        line = line.replace(k, "")

    for k in line.split(" "):
        elements[k.split(":")[0]] = float(k.split(":")[1])
    props["molecular_weight"] = _get_mol_weight_from_elements(elements)

    line = [
        k
        for k in "".join(
            [" ".join(k.strip().split()) for k in species_description]
        ).split("=")
        if "NASA" in k
    ][0]
    line = line.split("NASA")

    for k in line:
        k = [j for j in k.split("(") if j]
        if k:
            k = k[0].split(")")[0]
            k = " ".join([j for j in k.split("]") if j])
            k = [j.replace(",", " ").strip() for j in k.split("[") if j]
            if len(k) == 2:
                t_1 = float(k[0].split()[0])
                t_2 = float(k[0].split()[1])
                if t_1 >= 1000.0:
                    zone = "high"
                    t_range["mid"] = t_1
                    t_range["max"] = t_2
                else:
                    zone = "low"
                    t_range["min"] = t_1
                    t_range["mid"] = t_2
                coeffs[zone] = np.array([j for j in k[1].split() if j], dtype=float)

    nasa = _NasaPolys(coeffs, t_range, props["molecular_weight"])
    props["total_energy"] = nasa.get_total_energy
    props["total_enthalpy"] = nasa.get_total_enthalpy
    props["atoms"] = elements
    return props


class Species:
    """
    Class holding species properties
    """

    def __init__(self, mol_weight, enthalpy_func, energy_func, atoms=None):
        """
        Instanciation of Species object

            Parameters :
            ==========
            species_name : species name
            molecular_weight : species molecular weight
            total_energy : a temperature function returning species
                                total energy
            total_enthalpy : a temperature function returning species
                                total enthalpy
        """
        self.total_enthalpy_func = enthalpy_func
        self.total_energy_func = energy_func
        self.molecular_weight = mol_weight
        self.atoms = atoms

    def total_energy(self, temp):
        """
        Computing species total energy

        :param temperature: Temperature at which energy is evaluated

        :returns: **energy** - Array of species total energy at temperature *temp*
        """
        return self.total_energy_func(temp)

    def total_enthalpy(self, temp):
        """
        Computing species total enthalpy

        :param temperature: Temperature at which enthalpy is evaluated
        :type temperature: float

        :returns: **enthalpy** - Array of species total enthalpy at temperature *temp*

        """

        return self.total_enthalpy_func(temp)

    def c_p(self, temp):
        """
        Computing Specific heat at constant pressure

        :param temperature: Temperature at which C_p is evaluated

        :returns: **C_p** - Array of C_p at temperature *temp* in [J/(kg K)]
        """
        return (
            self.total_enthalpy_func(temp + 1.0) - self.total_enthalpy_func(temp - 1.0)
        ) * 0.5

    def c_v(self, temp):
        """
        Computing Specific heat at constant volume

        :param temperature: Temperature at which C_v is evaluated

        :returns: **C_v** - Array of C_v at temperature *temp* in [J/(kg K)]
        """
        return (
            self.total_energy_func(temp + 1.0) - self.total_energy_func(temp - 1.0)
        ) * 0.5

    def gamma(self, temp):
        """
        Computing Specific specific heat ratio

        :param temperature: Temperature at which gamma is evaluated

        :returns: **gamma** - Array of gamma at temperature *temp*
        """
        gamma = self.c_p(temp) / self.c_v(temp)

        return gamma


def build_thermo_from_avbp(database_file):
    """
    *Reading all AVBP database species and storing in a dict( ) \
    whose keys are species names*

    :param database_file: Full path to database file
    :type database_file: str

    :returns: **species** -  A dict( ) of Species objects whose keys are species names
    """
    species = dict()
    _db_stream, indexes = _get_species_indexes(database_file, "avbp")

    for i, _ in enumerate(indexes, 0):
        start = indexes[i]
        if i < len(indexes) - 1:
            end = indexes[i + 1]
        else:
            end = len(_db_stream)

        species_description = [line for line in _db_stream[start:end] if " = " in line]
        props = _make_props_avbp(species_description)
        species[props["species_name"]] = Species(
            props["molecular_weight"],
            props["total_enthalpy"],
            props["total_energy"],
            atoms=props["atoms"],
        )
    return species


def build_thermo_from_chemkin(database_file):
    """
    *Reading all* **CHEMKIN** *database species and storing in a dict( ) \
    whose keys are species names.*

    :param database_file: Full path to database file
    :type database_file: str

    :returns: **species** - A dict( ) of Species objects whose keys are species names.
    """
    species = dict()
    _db_stream, indexes = _get_species_indexes(database_file, "chemkin")

    for i in indexes:
        species_description = _db_stream[i : i + 4]
        props = _make_props_chemkin(species_description)
        species[props["species_name"]] = Species(
            props["molecular_weight"],
            props["total_enthalpy"],
            props["total_energy"],
            atoms=props["atoms"],
        )
    return species


def build_thermo_from_cantera(database_file):
    """
    *Reading all* **CANTERA** *database species and storing in a dict( ) \
    whose keys are species names*

    :param database_file: Full path to database file
    :type database_file: str

    :returns: **species** - A dict( ) of Species objects whose keys are species names
    """

    species = dict()
    _db_stream, indexes = _get_species_indexes(database_file, "cantera")

    n_species = len(indexes)
    indexes.append(len(_db_stream))

    for i in range(n_species):
        species_description = _db_stream[indexes[i] : indexes[i + 1]]
        props = _make_props_cantera(species_description)
        species[props["species_name"]] = Species(
            props["molecular_weight"],
            props["total_enthalpy"],
            props["total_energy"],
            atoms=props["atoms"],
        )
    return species
