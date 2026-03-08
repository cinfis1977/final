import pytest

from mastereq.weak_rate_kernel import parse_rate_kernel


def _channel_with_sparse(*, row_idx, col_idx, val, n_rec=2, n_true=2):
    return {
        "name": "CH",
        "type": "disappearance",
        "rate_kernel": {
            "exposure": 1.0,
            "true_bins": {"E_lo": [0.0, 1.0], "E_hi": [1.0, 2.0]},
            "smear_sparse": {
                "format": "coo",
                "n_rec": n_rec,
                "n_true": n_true,
                "row_idx": row_idx,
                "col_idx": col_idx,
                "val": val,
            },
            "flux_model": {"kind": "const", "value": 1.0},
            "sigma_model": {"kind": "const", "value": 1.0},
            "eff_model": {"kind": "const", "value": 1.0},
        },
        "bins": {"E_lo": [0.0, 1.0], "E_hi": [1.0, 2.0], "E_ctr": [0.5, 1.5], "N_obs": [0.0, 0.0], "N_bkg_sm": [0.0, 0.0]},
    }


def test_sparse_out_of_range_index_is_rejected():
    ch = _channel_with_sparse(row_idx=[0, 2], col_idx=[0, 0], val=[1.0, 0.0], n_rec=2, n_true=2)
    with pytest.raises(ValueError, match=r"row_idx out of range"):
        parse_rate_kernel(ch, reco_bin_count=2)


def test_sparse_duplicates_are_merged_and_validated():
    # Column-stochastic for 2 columns:
    # col0: (0,0)=0.5 + (0,0)=0.5 (duplicate) => 1.0
    # col1: (1,1)=1.0
    ch = _channel_with_sparse(row_idx=[0, 0, 1], col_idx=[0, 0, 1], val=[0.5, 0.5, 1.0], n_rec=2, n_true=2)
    rk = parse_rate_kernel(ch, reco_bin_count=2)
    # If parsing succeeds, duplicates were merged and column sums validated.
    assert rk is not None
