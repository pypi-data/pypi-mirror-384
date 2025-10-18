"""
This script calculate mass_fraction of species from a Phi
"""

__all__ = ["yk_from_phi", "phi_from_far"]


YO2_IN_AIR = 0.2314

MOLAR_MASSES = {"C": 0.0120107, "H": 0.00100797, "O2": 0.0319988, "N2": 0.0280134}


def far_stochio(c_x: float, h_y: float) -> float:
    """Return the fuel air ratio stoechiometric according to c_x h_y

    valid for AIR , not for PURE OXYGEN!!!

    BTW, the example in https://en.wikipedia.org/wiki/Air%E2%80%93fuel_ratio is for pure oxygen...
    """
    mass_mol_fuel = c_x * MOLAR_MASSES["C"] + h_y * MOLAR_MASSES["H"]
    coeff_o2 = c_x + (h_y / 4)
    coef_air = 1.0 / YO2_IN_AIR
    afr_sto = coef_air * (coeff_o2 * MOLAR_MASSES["O2"]) / mass_mol_fuel
    far_sto = 1.0 / afr_sto
    return far_sto


def phi_from_far(far: float, c_x: float, h_y: float) -> float:
    """
    *Return phi coefficient with the fuel air ratio coeff + fuel composition (Valid for AIR, Not  PURE OXYGEN!!)**

    :param far: the air-fuel ratio
    :type far: float
    :param c_x: stoechio coeff of Carbone
    :type c_x: float
    :param h_y: stoechio coeff of hydrogene
    :type h_y: float

    :returns:
        - **phi** - Equivalence ratio
    """
    return far / far_stochio(c_x, h_y)


def far_from_phi(phi: float, c_x: float, h_y: float) -> float:
    """
    *Return fuel air ratio coeff  with the phi coefficient + fuel composition (Valid for AIR, Not  PURE OXYGEN!!)*

    :param phi: eq. ratio coef
    :type far: float
    :param c_x: stoechio coeff of Carbone
    :type c_x: float
    :param h_y: stoechio coeff of hydrogene
    :type h_y: float

    :returns:
        - **far** - Equivalence ratio
    """
    return phi * far_stochio(c_x, h_y)


# use "fuel" here as default. Beware it important for pyavbp.
def yk_from_phi(phi: float, c_x: float, h_y: float, fuel_name: str = "fuel") -> float:
    """
    *Return the species mass fractions in a fresh fuel-air mixture (Valid for AIR, Not  PURE OXYGEN!!)*

    :param phi: equivalence ratio
    :type phi: float
    :param c_x: stoechio coeff of Carbone
    :type c_x: float
    :param h_y: stoechio coeff of hydrogene
    :type h_y: float
    :param fuel_name: Name of the fuel
    :type fuel_name: str

    :returns:
        - **y_k** - A dict of mass fractions

    """
    y_k = dict()
    if phi == 0.0:
        y_k[fuel_name] = 0.0
    else:
        afr_stochio = 1.0 / far_stochio(c_x, h_y)
        y_k[fuel_name] = 1.0 / (
            1.0
            + (1.0 + 3.76 * (MOLAR_MASSES["N2"] / MOLAR_MASSES["O2"]))
            * (afr_stochio / phi)
        )  # TNC Poinsot Veynante , pp 11-12

    y_air = 1 - y_k[fuel_name]
    y_k["N2"] = (1 - YO2_IN_AIR) * y_air
    y_k["O2"] = YO2_IN_AIR * y_air

    return y_k
