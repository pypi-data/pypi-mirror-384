""" unit tests for pyavbp.tools """

# import pytest
import numpy as np

# from ms_thermo.state import State
from ms_thermo.species import build_thermo_from_avbp, build_thermo_from_cantera


"""
************
Examples for State.
************

State is an object handling the Internal state of a CFD fluid, namely:
- density
- Total Energy
- Mass Fractions

Limits of State object
======================
Velocity is NOT partof the state object and must be treated separately.
State refer to a point (shape 1) or a set of points (shape n).
The spatial aspects, i.e. the position of the points,
or the mesh, must be handled separately.
"""
import numpy as np
from ms_thermo.state import State  # , build_thermo_from_cantera, build_thermo_from_avbp


def how_to_state_single():
    """

    live Example
    ============
    In the following a state for a single point is created
    using the primitive variables T, P, Y_k.
    """
    # Prerequisites : - a thermodynamic database (a default AVBP one is used)
    # species = build_thermo_from_cantera("./chem.cti")           #for cantera species database
    # species = build_thermo_from_chemkin("./thermo.dat")         #for chemkin species database
    # species = build_thermo_from_avbp("./species_database.dat")  #for avbp species database

    # State object initialization
    # basic : mass fractions, temperature, pressure setup
    # the variables can be in arrays of the same size
    state = State(
        temperature=600.0,  # Kelvin, optional, deaults to 300.
        pressure=100000.0,  # Pa, optional, defaults to 101325.
        mass_fractions_dict={"N2": 1.0},
    )  # ,#optional, defaults to {'O2':0.2325,'N2':0.7675}
    # species_db=species)     # defaults to the avbp species_database.dat from pyavbp

    # this shows the most common value, the minima and maxima of the current state variables
    print(state)

    # reachable variables
    print(state.energy)  # in J
    print(state.rho)  # in Kg.m^-3
    print(state.mass_fracs)  # no unit
    print(state.temperature)  # in K
    print(state.pressure)  # in Pa

    # those can be updated directly from energy or rho:
    state.energy = 216038.00954532798
    state.rho = 1.171918080399414

    # or from primitives : temperature, pressure, mass_fractions:
    state.mass_fracs = {
        "O2": 0.2325,
        "N2": 0.7675,
    }  # recomputes rho and mass fracs, keeps energy
    state.pressure = 101325.0  # recomputes density, keeps mass fractions and energy
    state.temperature = 300.0  # recomputes energy and density, keeps mass fractions

    # this can be useful to update the primitives all at once, or to ensure a meaningful state:
    state.update_state()

    # useful methods that does not update the state variables
    print(state.list_species())  # list of the species present in the mixture
    print(state.mix_energy(600.0))  # gets the energy (J) value at given temperature (K)
    print(
        state.mix_enthalpy(600.0)
    )  # gets the enthalpy (J) value at given temperature (K)
    print(
        state.mix_molecular_weight()
    )  # computes the total molecular weight of the mixture
    return state


def how_to_state_hundred():
    """

    live Example
    ============
    In the following a state for a hundred point is created
    using the primitive variables T, P, Y_k.
    """
    state = State(
        temperature=600.0 * np.ones(100),  # optional
        pressure=100000.0 * np.ones(100),  # optional
        mass_fractions_dict={"N2": 1.0 * np.ones(100)},
    )  # optional
    # WARNING be careful with the variables shapes, the main ones are energy, rho and mass_fracs
    state.update_state(
        temperature=300.0 * np.ones(100),  # optional
        pressure=101325.0 * np.ones(100),  # optional
        mass_fracs={"O2": 1.0 * np.ones(100)},
    )  # optional

    # this recomputes mass fractions (thus stores density and mass fractions)
    # then temperature (thus stores energy and density)
    # then pressure (thus stores density)
    return state


def how_to_state_conservatives():
    """

    live Example
    ============
    In the following a state for a single point is created
    using the conservative variables rho, rho_e, rho_y
    """
    # state can also be initalized from conservatives : rho, rho_e, rho_y in that order
    rho = 1.171918080399414
    rho_e = rho * 216038.00954532798
    rho_y = {"O2": 0.2325 * rho, "N2": 0.7675 * rho}
    state_cons = State.from_cons(rho, rho_e, rho_y)
    print(state_cons.temperature)
    print(state_cons.energy)
    print(state_cons.mix_energy(300.0))
    return state_cons


def test_species(datadir):
    """
    Test of the different databases loaders
    """
    database_file = datadir.join("species_database.dat")
    species = build_thermo_from_avbp(database_file)
    assert species["CH4"].molecular_weight == 0.0160423
    assert species["CH4"].total_enthalpy(300.0) == 628962.1812333644
    assert species["CH4"].total_energy(300.0) == 473480.1119540216
    assert species["CH4"].c_p(300.0) == 2253.1058514053584
    assert species["CH4"].c_v(300.0) == 1734.83228714086
    assert species["CH4"].gamma(300.0) == 1.2987456298260704

    database_file = datadir.join("chem.cti")
    species = build_thermo_from_cantera(database_file)
    assert species["CH4"].molecular_weight == 0.016043
    assert species["CH4"].total_enthalpy(300.0) == 664568.8428129908
    assert species["CH4"].total_energy(300.0) == 509093.55764188815
    assert species["CH4"].c_p(300.0) == 2229.001829937566
    assert species["CH4"].c_v(300.0) == 1710.7508793672314
    assert species["CH4"].gamma(300.0) == 1.3029377081261675


def test_state():
    """
    Unit tests of State
    """

    temperature = 300.0
    pressure = 101325.0
    mass_fracs = {"O2": 0.2325, "N2": 0.7675}
    energy = 216038.00954532798
    rho = 1.171918080399414
    enthalpy = 273041.4890558396
    mol_weight = 0.028848789032908505
    c_p = 1012.4558080496037
    c_v = 724.2530696082889
    gamma = 1.3979309864674632
    csound = 347.658253944254
    representation = "\nCurrent primitive state of the mixture \n"
    representation += "\t\t| Most Common |    Min    |    Max \n"
    representation += "----------------------------------------------------\n"
    representation += "             rho| 1.17192e+00 | 1.172e+00 | 1.172e+00 \n"
    representation += "          energy| 2.16038e+05 | 2.160e+05 | 2.160e+05 \n"
    representation += "     temperature| 3.00000e+02 | 3.000e+02 | 3.000e+02 \n"
    representation += "        pressure| 1.01325e+05 | 1.013e+05 | 1.013e+05 \n"
    representation += "            Y_O2| 2.32500e-01 | 2.325e-01 | 2.325e-01 \n"
    representation += "            Y_N2| 7.67500e-01 | 7.675e-01 | 7.675e-01 \n"

    state = how_to_state_single()
    assert state.temperature == temperature
    assert state.pressure == pressure
    assert state.mass_fracs == mass_fracs
    assert state.rho == rho
    assert state.energy == energy
    assert state.c_p == c_p
    assert state.c_v == c_v
    assert state.gamma == gamma
    assert state.csound == csound

    assert repr(state) == representation
    assert state.mix_molecular_weight() == mol_weight
    state.update_state()
    assert state.mass_fracs == mass_fracs
    assert state.rho == rho
    assert state.energy == energy

    state.mass_fracs = mass_fracs
    assert state.mass_fracs == mass_fracs
    state.temperature = temperature
    assert state.temperature == temperature
    state.pressure = pressure
    assert state.pressure == pressure

    state = how_to_state_hundred()
    np.testing.assert_allclose(
        state.mix_enthalpy(temperature * np.ones(100)), enthalpy * np.ones(100)
    )

    cons_state = how_to_state_conservatives()

    assert cons_state.temperature == temperature
    assert cons_state.pressure == pressure
    assert cons_state.mass_fracs == mass_fracs
    assert cons_state.rho == rho
    assert cons_state.mix_energy(temperature) == energy
