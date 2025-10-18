import pytest
from ms_thermo.yk_from_phi import yk_from_phi, far_from_phi, phi_from_far, far_stochio


def test_far_stochio():
    # test on kerosen
    cx = 9.7396
    hy = 20.0542
    afr_sr_ref = 14.870368526488049
    # afr_st = 1./far_st_ref
    # assert afr_st==afr_sr_ref  # AFR of Kerozen is around 15
    far_st_ref = 1.0 / afr_sr_ref

    far_st = far_stochio(cx, hy)
    assert far_st == far_st_ref


def test_far_from_phi():
    # test from SAE : FAR 102.57 /1000   <> Phi 1.51
    cx = 9.7396
    hy = 20.0542
    phi_ref = 1.51
    far = far_from_phi(phi_ref, cx, hy)
    assert far == 0.10154422180662784


def test_phi_from_far():
    # test from SAE : FAR 102.57 /1000   <> Phi 1.51
    cx = 9.7396
    hy = 20.0542
    far_ref = 0.10257
    phi = phi_from_far(far_ref, cx, hy)
    assert phi == 1.525253699761879


def test_ykfromphi():
    yf_methane = yk_from_phi(1.0, 1, 4, "CH4")["CH4"]
    yf_c3h8 = yk_from_phi(1.0, 3, 8, "C3H8")["C3H8"]
    yf_c8h18 = yk_from_phi(1.0, 8, 18, "C8H18")["C8H18"]
    yf_h2 = yk_from_phi(1.0, 0, 2, "H2")["H2"]

    assert pytest.approx(yf_methane, 0.00001) == 0.01333564942487222
    assert pytest.approx(yf_c3h8, 0.00001) == 0.014642729952608102
    assert pytest.approx(yf_c8h18, 0.00001) == 0.015164593008774152
    assert pytest.approx(yf_h2, 0.00001) == 0.006747884056174038
