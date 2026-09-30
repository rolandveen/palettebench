import numpy as np

from palettebench.colour import hex_to_srgb, relative_luminance, srgb_to_hex, srgb_to_lab
from palettebench.cvd import simulate_cvd


def test_hex_round_trip():
    assert srgb_to_hex(hex_to_srgb("#56B4E9")) == "#56B4E9"


def test_reference_black_white_lab_and_luminance():
    lab = srgb_to_lab(np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]))
    assert np.allclose(lab[:, 0], [0, 100], atol=0.02)
    assert np.allclose(relative_luminance(np.array([[0, 0, 0], [1, 1, 1]])), [0, 1])


def test_cvd_shape_range_and_zero_severity():
    rgb = np.array([[0.2, 0.4, 0.6], [1.0, 0.0, 0.0]])
    simulated = simulate_cvd(rgb, "protan", 50)
    assert simulated.shape == rgb.shape
    assert np.all((simulated >= 0) & (simulated <= 1))
    assert np.allclose(simulate_cvd(rgb, "deutan", 0), rgb, atol=1e-7)
