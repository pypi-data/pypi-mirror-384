import pytest
import numpy as np
from ms_thermo.kero_prim2cons import kero_prim2cons


def test_kero_prim2cons():
    rho, rhoE, rhoY = kero_prim2cons(300, 101325, 1)
    target_value_rho = 1.1858159472682281  # 1.2320962372505444
    target_value_rhoE = 256190.8849042345  # 266054.68156187434
    np.testing.assert_allclose(target_value_rho, rho, rtol=10e-6)
    np.testing.assert_allclose(target_value_rhoE, rhoE, rtol=10e-6)
