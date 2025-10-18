"""Module with functions helpers to  create gasout for CFD solvers"""

import yaml
import copy
import h5py
import numpy as np
from h5cross import hdfdict
import shutil
from importlib import resources
from ms_thermo.state import State


HEADLOG = """
   ### Gasout tool from ms_thermo package ###

    This is a demonstrator!
    It has not been thoroughy tested yet!

"""

__all__ = [
    "gasout_with_input",
    "gasout_dump_default_input",
    "alter_state",
    "spherical_tanh_mask",
    "directional_linear_mask",
    "fraction_z_mask",
    "load_mesh_and_solution",
    "save_data_for_avbp",
    "gasout_tool",
]


def alter_state(state, alpha, temp_new=None, press_new=None, y_new=None, verbose=False):
    """
    Apply gasout alterations to a State.

    :param state: State before alterations
    :type state: State
    :param alpha: Alteration mask with values from 0 (no alteration) to 1 (full alteration)
    :type alpha: ndarray or scalar
    :param temp_new: New temperature to apply, defaults to None
    :type temp_new: ndarray or scalar, optional
    :param press_new: New temperature to apply, defaults to None
    :type press_new: ndarray or scalar, optional
    :param y_new: New mass fractions to apply, defaults to None
    :type y_new: dict[str, ndarray or scalar], optional
    :param verbose: Verbosity, defaults to False
    :type verbose: bool, optional

    :returns: log, debug log
    :rtype: str
    """
    log = str()

    # Order may be important? According to commit d36c7348, Yk must be updated before T
    if y_new is not None:
        y_mix = dict()
        state_species = list(state.mass_fracs.keys())

        for spec in y_new:
            if spec not in state_species:
                msgerr = "\n\n Species mismatch:"
                msgerr += "\n" + str(spec) + " is not part of the mixture:\n"
                msgerr += "/".join(state_species)
                msgerr += "\nCheck your input file pretty please..."
                raise RuntimeWarning(msgerr)

        for spec in state.mass_fracs:
            value = 0
            if spec in y_new:
                value = y_new[spec]

            y_mix[spec] = state.mass_fracs[spec] + alpha * (
                value - state.mass_fracs[spec]
            )
        state.mass_fracs = y_mix

    if temp_new is not None:
        temp = np.array(state.temperature)
        state.temperature = temp + alpha * (temp_new - temp)

    if press_new is not None:
        state.pressure = state.pressure + alpha * (press_new - state.pressure)

    if verbose:
        footprint = 100.0 * np.sum(alpha) / alpha.shape[0]
        log += f"Footprint : {footprint: .3f} %"
    return log


def spherical_tanh_mask(coor, center, radius, delta):
    """
    Define a spherical mask. 0 inside the sphere, 1 outside, with a tanh transition.

    :param coor: Array of spatial coordinates (shape (n, ndim))
    :type coor: ndarray
    :param center: Array of sphere center coordinates (shape (ndim,))
    :type center: list, tuple or ndarray
    :param radius: Radius of the sphere
    :type radius: float
    :param delta: Transition thickness at the edge of the sphere
    :type delta: float

    :returns: alpha, alteration mask
    :rtype: ndarray
    """
    center = np.array(center)
    center_ndim = center.shape[0]
    coor_ndim = coor.shape[-1]
    if center_ndim != coor_ndim:
        msg_err = "\n\nDimension mismatch in the spherical center"
        msg_err += "\nCenter is " + str(center_ndim) + "D"
        msg_err += "\nCoords are " + str(coor_ndim) + "D"
        msg_err += "\nCheck your input file pretty please..."
        raise RuntimeWarning(msg_err)

    r_coor = np.linalg.norm(coor - center, axis=1)
    alpha = 0.5 * (1.0 - np.tanh((r_coor - radius) / (delta / 2)))
    return alpha


def directional_linear_mask(coor, axis, transition_start, transition_end):
    """
    Define a directional mask aligned with the `axis` coordinate axis.

    If `transition_end` > `transition_start`, the mask is 0 before `transition_start` and
    1 after `transition_end.
    If `transition_start` > `transition_end`, the mask is 1 before `transition_end` and
    0 after `transition_start.
    A linear transition is imposed between `transition_start` and `transition_end`.

    :param coor: Array of spatial coordinates (shape (n, ndim))
    :type coor: ndarray
    :param axis: Coordinate axis of the mask (0 x, 1 y, 2 z)
    :type axis: int
    :param transition_start: Start point of the linear mask
    :type transition_start: float
    :param transition_end: End point of the linear mask
    :type transition_end: float

    :returns: alpha, alteration mask
    :rtype: ndarray
    """
    direction = coor[:, axis]

    alpha = (direction - transition_start) / (transition_end - transition_start)
    alpha = np.clip(alpha, 0.0, 1.0)

    return alpha


def fraction_z_mask(
    state,
    specfuel,
    zmin,
    zmax,
    fuel_mass_fracs=None,
    oxyd_mass_fracs=None,
    atom_ref="C",
    verbose=False,
):
    """
    Compute a mask based on the mixture fraction Z.

    The mask is 1 between `zmin` and `zmax` and 0 outside.

    :param state: ms_thermo State object
    :type state: State
    :param specfuel: Fuel species name
    :type specfuel: str
    :param zmin: mask disabled (0) below this value
    :type zmin: float
    :param zmax: mask disabled (0) over this value
    :type zmax: float
    :param fuel_mass_fracs: Fuel mass fractions, defaults to composition at peak fuel concentration
    :type fuel_mass_fracs: dict, optional
    :param oxyd_mass_fracs: Oxydizer mass fractions, defaults to air
    :type oxyd_mass_fracs: dict, optional
    :param atom_ref: Reference atom, defaults to C
    :type atom_ref: str, optional
    :param verbose: Verbosity, defaults to False
    :type verbose: bool, optional

    :returns: alpha, alteration mask
    :rtype: ndarray
    """
    z_frac = state.compute_z_frac(
        specfuel,
        fuel_mass_fracs,
        oxyd_mass_fracs,
        atom_ref,
        verbose,
    )

    z_mid = 0.5 * (zmax + zmin)
    z_gap = 0.5 * (zmax - zmin)
    alpha = np.where(abs(z_frac - z_mid) < z_gap, 1.0, 0)
    return alpha


def gasout_with_input(coor, state, in_nob):
    """
    Update a State with gasout actions.

    :param coor: Array of spatial coordinates (shape (n, ndim))
    :type coor: ndarray
    :param state: ms_thermo State object
    :type state: State
    :param in_nob: Contents of the input file
    :type in_nob: dict

    :returns: Tuple containing the updated State and a log
    :rtype: tuple
    """

    log = str(HEADLOG)
    log += "\nInitial state"
    log += "\n ==========="
    log += "\n" + state.__repr__()

    for i, action in enumerate(in_nob["actions"]):

        log += "\n\nAction " + str(i) + ":" + action["type"]

        if action["type"] == "directional_linear_mask":
            reqd_keys = [
                "direction",
                "transition_start",
                "transition_stop",
            ]
            check = _check_action_params(reqd_keys, list(action.keys()))
            if check != "":
                raise RuntimeWarning(log + check)

            if action["direction"] == "x":
                axis = 0
            elif action["direction"] == "y":
                axis = 1
            elif action["direction"] == "z":
                axis = 2
            else:
                msgerr = "\n INPUT ERROR : " + "Direction must be one of x, y or z"
                raise RuntimeWarning(log + msgerr)

            alpha = directional_linear_mask(
                coor,
                axis=axis,
                transition_start=action["transition_start"],
                transition_stop=action["transition_stop"],
            )

        elif action["type"] == "spherical_tanh_mask":
            reqd_keys = [
                "center",
                "radius",
                "delta",
            ]
            check = _check_action_params(reqd_keys, list(action.keys()))
            if check != "":
                raise RuntimeWarning(log + check)

            alpha = spherical_tanh_mask(
                coor,
                center=action["center"],
                radius=action["radius"],
                delta=action["delta"],
            )

        elif action["type"] == "fraction_z_mask":
            reqd_keys = [
                "specfuel",
                "atom_ref",
                "oxyd_mass_fracs",
                "fuel_mass_fracs",
                "zmax",
                "zmin",
            ]

            check = _check_action_params(reqd_keys, list(action.keys()))
            if check != "":
                raise RuntimeWarning(log + check)

            alpha = fraction_z_mask(
                state,
                action["specfuel"],
                zmin=action["zmin"],
                zmax=action["zmax"],
                fuel_mass_fracs=action["fuel_mass_fracs"],
                oxyd_mass_fracs=action["oxyd_mass_fracs"],
                atom_ref=action["specfuel"],
                verbose=True,
            )

        if "new_temperature" not in action:
            action["new_temperature"] = None
        if "new_pressure" not in action:
            action["new_pressure"] = None
        if "new_yk" not in action:
            action["new_yk"] = None

        out = alter_state(
            state,
            alpha,
            temp_new=action["new_temperature"],
            press_new=action["new_pressure"],
            y_new=action["new_yk"],
            verbose=True,
        )
        log += "\n" + out

    log += "\n\n Final state"
    log += "\n ==========="

    log += "\n" + state.__repr__()

    return state, log


def gasout_dump_default_input(fname):
    """Dump the default gasout input file"""
    default_gasout_input = str(
        resources.files(__package__) / "INPUT/default_gasout_input.yml"
    )

    shutil.copyfile(default_gasout_input, fname)


def _check_action_params(reqd_keys, provided_keys):
    """
    Check gasout action keys

    :param reqd_keys: List of required keys
    :type reqd_keys: list[str]
    :param provided_keys: List of keys in the input file
    :type provided_keys: list[str]

    :returns: Log of the accepted and missing keys
    :rtype: str
    """
    log = str()
    for key in provided_keys:
        if key not in reqd_keys + ["type", "new_temperature", "new_pressure", "new_yk"]:
            log += "\n.   - key " + key + " not accepted"
    if log != "":
        log += "\n.  - Accepted keys"
        log += "\n.      >".join(reqd_keys)

    for key in reqd_keys:
        if key not in provided_keys:
            log += "\n key " + key + " is missing."
    return log


def load_mesh_and_solution(fname, mname):
    """
    Load a mesh and solution into HDF5 objects

    :param fname: Filename of the solution
    :type fname: str
    :param mname: Filename of the mesh
    :type mname: str
    """
    print("Reading solution in ", fname)
    with h5py.File(fname, "r") as fin:
        sol = hdfdict.load(fin, lazy=False)
    print("Reading mesh in ", mname)
    with h5py.File(mname, "r") as fin:
        mesh = hdfdict.load(fin, lazy=False)
    return mesh, sol


def build_data_from_avbp(mesh, sol):
    """
    Build coordinates and a State from an AVBP mesh and solution

    :param mesh: AVBP mesh
    :type mesh: HDF5 object
    :param sol: AVBP solution
    :type sol: HDF5 object

    :returns: Tuple of coordinates and State
    :rtype: tuple
    """
    state = State.from_cons(
        sol["GaseousPhase"]["rho"], sol["GaseousPhase"]["rhoE"], sol["RhoSpecies"]
    )

    x_coor = mesh["Coordinates"]["x"]
    y_coor = mesh["Coordinates"]["y"]
    try:
        z_coor = mesh["Coordinates"]["z"]
        coor = np.stack((x_coor, y_coor, z_coor), axis=-1)
    except KeyError:
        coor = np.stack((x_coor, y_coor), axis=-1)

    return coor, state


def save_data_for_avbp(state, sol, fname):
    """Update the full solution with the state parameters"""
    sol_new = copy.deepcopy(sol)
    sol_new["GaseousPhase"]["rho"] = state.rho
    sol_new["GaseousPhase"]["rhoE"] = state.rho * state.energy
    for spec in sol_new["RhoSpecies"]:
        sol_new["RhoSpecies"][spec] = state.rho * state.mass_fracs[spec]

    try:
        sol_new["Additionals"]["temperature"] = state.temperature
        sol_new["Additionals"]["pressure"] = state.pressure
    except KeyError:
        print("-Additionals- group is not part of the solution.")

    print("Saving solution in ", fname)
    with h5py.File(fname, "w") as fout:
        hdfdict.dump(sol_new, fout)


def gasout_tool(inputfile):
    """Main call"""

    with open(inputfile, "r") as fin:
        in_nob = yaml.load(fin, Loader=yaml.Loader)

    mesh, sol = load_mesh_and_solution(in_nob["inst_solut"], in_nob["mesh"])

    coor, state = build_data_from_avbp(mesh, sol)

    state_new, log = gasout_with_input(coor, state, in_nob)

    print(log)

    save_data_for_avbp(state_new, sol, in_nob["inst_solut_output"])
