import colour
import numpy as np
import pytest

from palettebench import analyse_palette, load_palette
from palettebench.analysis import AnalysisConfig


@pytest.mark.parametrize(
    ("lab1", "lab2", "expected"),
    [
        ([50.0, 2.6772, -79.7751], [50.0, 0.0, -82.7485], 2.0425),
        ([50.0, 3.1571, -77.2803], [50.0, 0.0, -82.7485], 2.8615),
        ([50.0, 2.8361, -74.0200], [50.0, 0.0, -82.7485], 3.4412),
        ([50.0, -1.3802, -84.2814], [50.0, 0.0, -82.7485], 1.0000),
        ([50.0, -1.1848, -84.8006], [50.0, 0.0, -82.7485], 1.0000),
        ([50.0, -0.9009, -85.5211], [50.0, 0.0, -82.7485], 1.0000),
        ([50.0, 0.0, 0.0], [50.0, -1.0, 2.0], 2.3669),
        ([50.0, -1.0, 2.0], [50.0, 0.0, 0.0], 2.3669),
        ([50.0, 2.49, -0.001], [50.0, -2.49, 0.0009], 7.1792),
        ([50.0, 2.49, -0.001], [50.0, -2.49, 0.0010], 7.1792),
        ([50.0, 2.49, -0.001], [50.0, -2.49, 0.0011], 7.2195),
        ([50.0, 2.49, -0.001], [50.0, -2.49, 0.0012], 7.2195),
        ([50.0, -0.001, 2.49], [50.0, 0.0009, -2.49], 4.8045),
        ([50.0, -0.001, 2.49], [50.0, 0.0010, -2.49], 4.8045),
        ([50.0, -0.001, 2.49], [50.0, 0.0011, -2.49], 4.7461),
        ([50.0, 2.5, 0.0], [50.0, 0.0, -2.5], 4.3065),
        ([50.0, 2.5, 0.0], [73.0, 25.0, -18.0], 27.1492),
        ([50.0, 2.5, 0.0], [61.0, -5.0, 29.0], 22.8977),
        ([50.0, 2.5, 0.0], [56.0, -27.0, -3.0], 31.9030),
        ([50.0, 2.5, 0.0], [58.0, 24.0, 15.0], 19.4535),
        ([50.0, 2.5, 0.0], [50.0, 3.1736, 0.5854], 1.0000),
        ([50.0, 2.5, 0.0], [50.0, 3.2972, 0.0], 1.0000),
        ([50.0, 2.5, 0.0], [50.0, 1.8634, 0.5757], 1.0000),
        ([50.0, 2.5, 0.0], [50.0, 3.2592, 0.3350], 1.0000),
        ([60.2574, -34.0099, 36.2677], [60.4626, -34.1751, 39.4387], 1.2644),
        ([63.0109, -31.0961, -5.8663], [62.8187, -29.7946, -4.0864], 1.2630),
        ([61.2901, 3.7196, -5.3901], [61.4292, 2.2480, -4.9620], 1.8731),
        ([35.0831, -44.1164, 3.7933], [35.0232, -40.0716, 1.5901], 1.8645),
        ([22.7233, 20.0904, -46.6940], [23.0331, 14.9730, -42.5619], 2.0373),
        ([36.4612, 47.8580, 18.3852], [36.2715, 50.5065, 21.2231], 1.4146),
        ([90.8027, -2.0831, 1.4410], [91.1528, -1.6435, 0.0447], 1.4441),
        ([90.9257, -0.5406, -0.9208], [88.6381, -0.8985, -0.7239], 1.5381),
        ([6.7747, -0.2908, -2.4247], [5.8714, -0.0985, -2.2286], 0.6377),
        ([2.0776, 0.0795, -1.1350], [0.9033, -0.0636, -0.5514], 0.9082),
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


@pytest.mark.parametrize(
    "kwargs",
    [
        {"severities": ()},
        {"severities": (20, 20)},
        {"severities": (True,)},
        {"thresholds": (-1.0,)},
        {"thresholds": (float("nan"),)},
        {"thresholds": (10.0, 5.0)},
        {"thresholds": (5.0, 5.0)},
        {"curve_step": 0},
        {"weakest_count": 0},
    ],
)
def test_analysis_config_rejects_invalid_values(kwargs):
    with pytest.raises((TypeError, ValueError)):
        AnalysisConfig(**kwargs)


def test_cvd_gamut_clipping_is_retained_for_provenance():
    result = analyse_palette(load_palette("palettes/okabe-ito.yaml"))
    protan = next(condition for condition in result.conditions if condition.key == "protan100")
    assert np.count_nonzero(protan.clipped_channels.any(axis=1)) == 2
    assert protan.raw_srgb.min() < 0
    assert np.all((protan.srgb >= 0) & (protan.srgb <= 1))
