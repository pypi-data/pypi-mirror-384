#!/usr/bin/env python
"""
cli.py
Command line interface for tools in ms_thermo
"""

import click
import ms_thermo


def add_version(f):
    """
    Add the version of the tool to the help heading.
    :param f: function to decorate
    :return: decorated function
    """
    doc = f.__doc__
    f.__doc__ = (
        "Package " + ms_thermo.__name__ + " v" + ms_thermo.__version__ + "\n\n" + doc
    )
    return f


@click.group()
@add_version
def main_cli():
    """---------------    MS_THERMO  --------------------

    You are now using the Command line interface of MS-Thermo,
    a Python3 helper for reactive multispecies computation, created at CERFACS (https://cerfacs.fr).

    This is a python package currently installed in your python environement.
    See the full documentation at : https://ms-thermo.readthedocs.io/en/latest/.
    """
    pass


@click.command(help="Renamed as kero-tadia", deprecated=True)
@click.argument("temperature", nargs=1)
@click.argument("pressure", nargs=1)
@click.argument("phi", nargs=1)
def tadia(temperature, pressure, phi):
    return


main_cli.add_command(tadia)


@click.command()
@click.argument("temperature", nargs=1)
@click.argument("pressure", nargs=1)
@click.argument("phi", nargs=1)
def kero_tadia(temperature, pressure, phi):
    """Adiabatic flame temperature for a kerosene-air mixture.

    The initial TEMPERATURE is in Kelvins.
    The initial PRESURE in in Pascals.
    The PHI equivalence ratio equals 1 at stoechiometry.

    The computation is done by interpolation in a precomputed 2S_KERO_BFER table.
    The system considered to build the table was a 1D flame at constant pressure.
    """
    from ms_thermo.tadia import tadia_table

    burnt_temperature, yk_ = tadia_table(
        float(temperature), float(pressure), float(phi)
    )
    print(
        "\nThe adiabatic flame temperature of a mix "
        + f"C10H22-air from tables is : {burnt_temperature:.2f} K."
    )
    print("\nSpecies     |    Mass fraction")
    print("------------------------------")
    for specie in yk_:
        print(f"{specie:12s}|       {yk_[specie]:.3f}")


main_cli.add_command(kero_tadia)


@click.command(help="Renamed as kero-prim2cons", deprecated=True)
@click.argument("temperature", nargs=1, type=float)
@click.argument("pressure", nargs=1, type=float)
@click.argument("phi", nargs=1, type=float)
def fresh_gas(temperature, pressure, phi):
    return


main_cli.add_command(fresh_gas)


@click.command()
@click.argument("temperature", nargs=1, type=float)
@click.argument("pressure", nargs=1, type=float)
@click.argument("phi", nargs=1, type=float)
def kero_prim2cons(temperature, pressure, phi):
    """Primitive to conservative variable conversion for a kerosene-air mixture.

    The initial TEMPERATURE is in Kelvins.
    The initial PRESURE in in Pascals.
    The PHI equivalence ratio equals 1 at stoechiometry.

    The computation is done using a 100K piecewise linear table of enthalpies.
    """
    from ms_thermo.kero_prim2cons import kero_prim2cons

    rho, rhoE, rhoyk = kero_prim2cons(temperature, pressure, phi)
    print(f"\nrho       |  {rho:.3f} kg/m3")
    print(f"rhoE      |  {rhoE:.3f} J.kg/m3")
    print("rhoYk     |")
    for specie in rhoyk:
        print(f" {specie:9s}|  {rhoyk[specie]:.3f} mol.kg/m3")
    print("------------------------------")
    print("Yk        |")
    for specie in rhoyk:
        print(f" {specie:9s}|  {rhoyk[specie]/rho:.3f} [-]")


main_cli.add_command(kero_prim2cons)


@click.command()
@click.argument("temperature", nargs=1, type=float)
@click.argument("pressure", nargs=1, type=float)
@click.argument("phi", nargs=1, type=float)
@click.argument("fuel_name", nargs=1)
@click.argument("c_x", nargs=1, type=float)
@click.argument("h_y", nargs=1, type=float)
@click.argument("path2cti", nargs=1)
def hp_equil(temperature, pressure, phi, fuel_name, c_x, h_y, path2cti):
    """HP equilibrium using Cantera.

    The initial TEMPERATURE is in Kelvins.
    The initial PRESURE in in Pascals.
    The PHI equivalence ratio equals 1 at stoechiometry.
    The FUEL_NAME is the name of the fuel in your system.
    The path2cti is the path to your .CTI file.

    The computation is done using the Cantera library
    installed on your environement (not included in this package)
    The system considered is an HP equilibrium.

    See http://www.cerfacs.fr/cantera/ for more information and some .CTI files

    """
    from ms_thermo.tadia import tadia_cantera

    burnt_temperature, yk_ = tadia_cantera(
        temperature, pressure, phi, c_x, h_y, fuel_name, path2cti
    )
    print(
        "\nThe adiabatic flame temperature of a mix "
        + f"{str(fuel_name)}-air from cantera is : {burnt_temperature:.2f} K."
    )
    print("\nSpecies     |    Mass fraction")
    print("------------------------------")
    nb_other_species = 0
    y_other_species = 0
    for specie in yk_:
        if yk_[specie] < 1e-3:
            nb_other_species += 1
            y_other_species += yk_[specie]
        else:
            print(f"{specie:12s}|       {yk_[specie]:.3f}")
    print(f"+ {nb_other_species} others |       {y_other_species:.3f}")


main_cli.add_command(hp_equil)


@click.command()
@click.argument("phi", nargs=1, type=float)
@click.argument("c_x", nargs=1, type=float)
@click.argument("h_y", nargs=1, type=float)
@click.argument("fuel_name", nargs=1)
def yk_from_phi(phi, c_x, h_y, fuel_name):
    """Mass fractions of a fuel-air mixture.

    The PHI equivalence ratio equals 1 at stoechiometry.
    C_X is the number of carbon atoms in your fuel.
    H_Y is the number of hydrogen atoms in your fuel
    FUEL_NAME is the name of fuel species.
    """
    from ms_thermo.yk_from_phi import yk_from_phi

    yk_ = yk_from_phi(float(c_x), float(h_y), float(phi), str(fuel_name))
    print("\nSpecies     |    Mass fraction")
    print("------------------------------")
    for specie in yk_:
        print(f"{specie:12s}|       {yk_[specie]:.3f}")


main_cli.add_command(yk_from_phi)


@click.command()
@click.option("--new", is_flag=True, help="prefill INPUTFILE with default values")
@click.argument("inputfile", nargs=1)
def gasout(inputfile, new):
    """Apply GASOUT actions to a mixture.

    A GASOUT action is a local alteration of the thermodynamical
    state (temperature, pressure or mixture) of a mixture.

    The INPUTFILE, in .yaml format, controls the list of actions.
    Create a new INPUTFILE with the --new flag to see all possibilities.
    """
    from ms_thermo.gasout import gasout_dump_default_input, gasout_tool

    if new:
        gasout_dump_default_input(inputfile)
    else:
        gasout_tool(inputfile)


main_cli.add_command(gasout)
