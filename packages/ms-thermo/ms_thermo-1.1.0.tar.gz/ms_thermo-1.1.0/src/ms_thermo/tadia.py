from ms_thermo.flame_params import FlameTable
from ms_thermo.yk_from_phi import yk_from_phi
from importlib import resources


__all__ = ["tadia_cantera", "tadia_table"]


def tadia_table(
    t_fresh_gases, p_fresh_gases, phi, fuel=None, fuel_name="KERO", c_x=10, h_y=20
):
    """
    *Compute the adiabatic flame temperature of a premixed kero/air mixture from tables*

    :param t_fresh_gases: Temperature of the fresh gases [K]
    :type t_fresh_gases: float
    :param p_fresh_gases: Pressure of the fresh gases [Pa]
    :type p_fresh_gases: float
    :param phi: Equivalence ratio [-]
    :type phi: float
    :param fuel: path to flame table AVBP
    :type fuel: str
    :param fuel_name: Name of the fuel species
    :type fuel_name: str
    :param c_x: nb. of C atoms
    :type c_x: float
    :param h_y: nb. of H atoms
    :type h_y: float

    :returns:
        - **t_burnt_gases** - Temperature of the burnt gases
        - **yk_burnt** - Dict of mass fractions of burnt gases
    """

    case = FlameTable()

    mass_molar = {"C": 0.0120107, "H": 0.00100797, "O2": 0.0319988, "N2": 0.0280134}

    if fuel is None:
        fuel_table = str(resources.files(__package__) / "INPUT/2S_KERO_BFER.h5")
        c_x = 10.0
        h_y = 20.0
    else:
        fuel_table = fuel

    yk_fresh = yk_from_phi(phi, c_x, h_y, fuel_name)

    mass_mol_fuel = c_x * mass_molar["C"] + h_y * mass_molar["H"]
    coeff_o2 = c_x + (h_y / 4)
    stoechio = coeff_o2 * mass_molar["O2"] / mass_mol_fuel

    yk_burnt = dict()
    yk_burnt["N2"] = yk_fresh["N2"]

    if phi <= 1:
        yk_burnt[fuel_name] = 0.0
        yk_burnt["O2"] = yk_fresh["O2"] - stoechio * yk_fresh[fuel_name]
        yk_burnt["CO2"] = (
            c_x
            * yk_fresh[fuel_name]
            * (mass_molar["O2"] + mass_molar["C"])
            / mass_mol_fuel
        )
        yk_burnt["H2O"] = (
            h_y
            / 2
            * yk_fresh[fuel_name]
            * (0.5 * mass_molar["O2"] + 2 * mass_molar["H"])
            / mass_mol_fuel
        )
    else:
        yk_burnt[fuel_name] = yk_fresh[fuel_name] - yk_fresh["O2"] / stoechio
        yk_burnt["O2"] = 0.0
        yk_burnt["CO2"] = (
            (1 / (1 + h_y / (4 * c_x)))
            * yk_fresh["O2"]
            * (mass_molar["O2"] + mass_molar["C"])
            / mass_molar["O2"]
        )
        yk_burnt["H2O"] = (
            (1 / (1 / 2 + 2 * c_x / h_y))
            * yk_fresh["O2"]
            * (0.5 * mass_molar["O2"] + 2 * mass_molar["H"])
            / mass_molar["O2"]
        )

    case.read_table_hdf(fuel_table)
    case.get_params(phi, t_fresh_gases, p_fresh_gases)

    t_burnt_gases = case.interpolated_data_dict["TEMPERATURE_BURNT"][0]

    return t_burnt_gases, yk_burnt


def tadia_cantera(t_fresh_gases, p_fresh_gases, phi, c_x, h_y, fuel_name, cti_file):
    """
    *Compute the adiabatic flame temperature of a premixed fuel/air mixture from Cantera*

    :param t_fresh_gases: Temperature of the fresh gases [K]
    :type t_fresh_gases: float
    :param p_fresh_gases: Pressure of the fresh gases [Pa]
    :type p_fresh_gases: float
    :param phi: Equivalence ratio [-]
    :type phi: float
    :param c_x: nb. of C atoms
    :type c_x: float
    :param h_y: nb. of H atoms
    :type h_y: float
    :param fuel_name: Name of the fuel species
    :type fuel_name: string
    :param cti_file: Path to the cti file to consider
    :type cti_file: string

    :returns:
        - **t_burnt_gases** - Temperature of the burnt gases
        - **yk_burnt** - Dict of mass fractions of burnt gases

    .. note:: **Warning**: This function may not be available if you do not have cantera in your environment
    """
    try:
        import cantera as ct
    except ModuleNotFoundError:
        print("Cantera module is not installed.")
        print("See instructions on http://www.cerfacs.fr/cantera/installation.php")
        raise ModuleNotFoundError
    case = ct.Solution(cti_file)
    case.Y = yk_from_phi(phi, c_x, h_y, fuel_name)
    case.TP = t_fresh_gases, p_fresh_gases
    case.equilibrate("HP")
    t_burnt_gases = case.T
    yk_burnt = case.mass_fraction_dict()
    return t_burnt_gases, yk_burnt
