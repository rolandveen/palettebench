import colour
import numpy as np
import pytest

from palettebench import analyse_palette, load_palette


@pytest.mark.parametrize(
    ("lab1", "lab2", "expected"),
    [
        ([50.0, 2.6772, -79.7751], [50.0, 0.0, -82.7485], 2.0425),
        ([50.0, 3.1571, -77.2803], [50.0, 0.0, -82.7485], 2.8615),
        ([50.0, 2.8361, -74.0200], [50.0, 0.0, -82.7485], 3.4412),
        ([50.0, -1.3802, -84.2814], [50.0, 0.0, -82.7485], 1.0000),
        ([50.0, -1.1848, -84.8006], [50.0, 0.0, -82.7485], 1.0000),
        ([50.0, -0.9009, -85.5211], [50.0, 0.0, -82.7485], 1.0000),
    ],
)
def test_ciede2000_reference_pairs(lab1, lab2, expected):
    assert float(colour.delta_E(lab1, lab2, method="CIE 2000")) == pytest.approx(expected, abs=5e-5)


def test_pairwise_matrices_are_symmetric_with_zero_diagonal():
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    for condition in result.conditions:
        assert np.allclose(condition.delta_e, condition.delta_e.T)
        assert np.allclose(np.diag(condition.delta_e), 0)


def test_threshold_counts_have_matching_fractions():
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    for summary in result.summaries:
        for threshold, count in summary.below.items():
            assert summary.below_fraction[threshold] == pytest.approx(count / summary.pair_count)
