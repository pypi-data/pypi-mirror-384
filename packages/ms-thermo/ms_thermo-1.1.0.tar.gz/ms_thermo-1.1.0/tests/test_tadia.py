import numpy as np
from ms_thermo.tadia import tadia_table


def test_tadia_table():

    burned_t, yburnt = tadia_table(300, 101325, 1)
    target_value = 2312.990462472097

    np.testing.assert_allclose(target_value, burned_t, rtol=10e-6)
    print([k for k in yburnt.values()])
    target_value = [
        0.7566773271356266,
        0.0,
        0.17472881177111413,
        0.048670525063567914,
        0.019923336029691263,
    ]
    np.testing.assert_allclose(target_value, [k for k in yburnt.values()], rtol=10e-6)
