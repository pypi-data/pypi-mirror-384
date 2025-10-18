""" Module testing SpeciesState and MixtureState """

import numpy as np
import pytest

from ms_thermo.mixture_state import SpeciesState, MixtureState

DIM1 = 5


def test_mixture_state():
    """test of SpeciesAtomic and MixtureAtomic classes"""

    ATOMIC_MASS = {"C": 12.0107, "H": 1.00784, "O": 15.999, "N": 14.0067}

    def compute_mass_frac(phi, fuel, n_c, n_h):
        m_fuel = max((phi - 1) * (n_c * ATOMIC_MASS["C"] + n_h * ATOMIC_MASS["H"]), 0.0)
        m_o2 = max((1 - phi) * (n_c + n_h / 4) * 2 * ATOMIC_MASS["O"], 0.0)
        m_n2 = (n_c + n_h / 4) * 3.76 * 2 * ATOMIC_MASS["N"]
        m_co2 = phi * n_c * (ATOMIC_MASS["C"] + 2 * ATOMIC_MASS["O"])
        m_h2o = phi * n_h / 2 * (2 * ATOMIC_MASS["H"] + ATOMIC_MASS["O"])

        msum = m_fuel + m_o2 + m_n2 + m_co2 + m_h2o
        species_dict = {}
        species_dict[fuel] = m_fuel / msum * np.ones(DIM1)
        species_dict["O2"] = m_o2 / msum * np.ones(DIM1)
        species_dict["N2"] = m_n2 / msum * np.ones(DIM1)
        species_dict["CO2"] = m_co2 / msum * np.ones(DIM1)
        species_dict["H2O"] = m_h2o / msum * np.ones(DIM1)

        return species_dict

    fuel = "C10H20"
    phi = 1.0
    species_dict = compute_mass_frac(phi, fuel, 10, 20)
    mixture = MixtureState(species_dict, fuel)

    assert len(mixture.species) == 5
    assert isinstance(mixture.species[0], SpeciesState)
    assert mixture.species_name == [fuel, "O2", "N2", "CO2", "H2O"]
    np.testing.assert_allclose(mixture.mixture_fraction, 0.063775, atol=1e-6)
    np.testing.assert_allclose(mixture.equivalence_ratio, phi)
    np.testing.assert_allclose(mixture.far, 0.06812, atol=1e-6)
    np.testing.assert_allclose(mixture.far_st, 0.06812, atol=1e-6)
    np.testing.assert_allclose(mixture.afr, 14.680006, atol=1e-6)

    phi = 0.5
    species_dict = compute_mass_frac(phi, fuel, 10, 20)
    mixture = MixtureState(species_dict, fuel)
    np.testing.assert_allclose(mixture.mixture_fraction, 0.03295, atol=1e-6)
    np.testing.assert_allclose(mixture.equivalence_ratio, phi, atol=2e-4, rtol=4e-4)
    np.testing.assert_allclose(mixture.far, 0.034073, atol=1e-6)
    np.testing.assert_allclose(mixture.far_st, 0.06812, atol=1e-6)
    np.testing.assert_allclose(mixture.afr, 29.348641, atol=1e-6)

    with pytest.raises(NameError):
        mixture.species_by_name("dummy")

    species_dict["N2"] /= 2.0
    with pytest.raises(RuntimeError):
        mixture = MixtureState(species_dict, fuel)
