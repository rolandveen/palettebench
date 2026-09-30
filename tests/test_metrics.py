import colour
import numpy as np
import pytest

from palettebench import analyse_palette, load_palette


def test_ciede2000_reference_pair():
    lab1 = np.array([50.0, 2.6772, -79.7751])
    lab2 = np.array([50.0, 0.0, -82.7485])
    assert float(colour.delta_E(lab1, lab2, method="CIE 2000")) == pytest.approx(2.0425, abs=5e-5)


def test_pairwise_matrices_are_symmetric_with_zero_diagonal():
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    for condition in result.conditions:
        assert np.allclose(condition.delta_e, condition.delta_e.T)
        assert np.allclose(np.diag(condition.delta_e), 0)
