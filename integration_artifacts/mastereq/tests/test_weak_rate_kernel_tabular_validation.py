import numpy as np
import pytest

from mastereq.weak_rate_kernel import parse_rate_kernel


def _base_channel() -> dict:
    return {
        "name": "CH",
        "type": "disappearance",
        "rate_kernel": {
            "exposure": 1.0,
            "tabular_coverage": "strict",
            "true_bins": {"E_lo": [0.0, 1.0], "E_hi": [1.0, 3.0]},
            "smear_rec_by_true": [[1.0, 0.0], [0.0, 1.0]],
            "flux_model": {"kind": "tabular", "E_lo": [0.0, 1.0], "E_hi": [1.0, 3.0], "y": [1.0, 1.0]},
            "sigma_model": {"kind": "tabular", "E_lo": [0.0, 1.0], "E_hi": [1.0, 3.0], "y": [1.0, 1.0]},
            "eff_model": {"kind": "tabular", "E_lo": [0.0, 1.0], "E_hi": [1.0, 3.0], "y": [1.0, 1.0]},
        },
        "bins": {"E_lo": [0.0, 1.0], "E_hi": [1.0, 3.0], "E_ctr": [0.5, 2.0], "N_obs": [0.0, 0.0], "N_bkg_sm": [0.0, 0.0]},
    }


def test_tabular_negative_y_is_rejected():
    ch = _base_channel()
    ch["rate_kernel"]["flux_model"]["y"] = [1.0, -0.1]
    with pytest.raises(ValueError, match=r"nonnegative"):
        parse_rate_kernel(ch, reco_bin_count=2)


def test_tabular_strict_coverage_rejects_missing_support():
    ch = _base_channel()
    # flux only covers [0,1], but true bins include [1,3]
    ch["rate_kernel"]["flux_model"] = {"kind": "tabular", "E_lo": [0.0], "E_hi": [1.0], "y": [1.0]}
    with pytest.raises(ValueError, match=r"does not fully cover"):
        parse_rate_kernel(ch, reco_bin_count=2)


def test_tabular_rejects_nonfinite_y():
    ch = _base_channel()
    ch["rate_kernel"]["sigma_model"]["y"] = [np.nan, 1.0]
    with pytest.raises(ValueError, match=r"non-finite"):
        parse_rate_kernel(ch, reco_bin_count=2)
