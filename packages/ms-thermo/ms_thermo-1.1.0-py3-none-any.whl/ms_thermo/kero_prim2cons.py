from ms_thermo.state import State
from ms_thermo.yk_from_phi import yk_from_phi

__all__ = ["kero_prim2cons"]


def kero_prim2cons(temperature, pressure, phi):
    """
    Compute conservative variables from primitive variables in a kerosene-air mixture.

    :param temperature: the fresh gas temperature
    :type temperature: float
    :param pressure: pressure of the fresh gas
    :type pressure: float
    :param phi: equivalence ratio of the air-fuel mixture
    :type phi: float
    :param fuel: fuel
    :type fuel: string

    :returns:
        - **rho** - Density
        - **rhoE** - Conservative energy
        - **rhoyk** - Dict of conservative mass fractions

    """
    yk = yk_from_phi(
        phi, 10, 22, "KERO"
    )  # This can be adapted to any simple hydrocarbon fuel

    gas = State(None, temperature, pressure, yk)
    rho = gas.rho
    rhoE = gas.rho * gas.energy
    rhoyk = dict()
    for specie in gas._y_k.keys():
        rhoyk[specie] = gas.rho * gas._y_k[specie]
    return rho, rhoE, rhoyk
