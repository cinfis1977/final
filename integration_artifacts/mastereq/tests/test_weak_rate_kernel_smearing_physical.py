import numpy as np
import pytest

from mastereq.weak_rate_kernel import validate_physical_smearing


def test_smearing_matrix_physical_constraints_pass():
    S = np.array([[0.8, 0.2], [0.2, 0.8]], dtype=float)
    validate_physical_smearing(S)


def test_smearing_matrix_rejects_negative_entries():
    S = np.array([[1.0, -0.1], [0.0, 1.1]], dtype=float)
    with pytest.raises(ValueError, match="negative"):
        validate_physical_smearing(S)


def test_smearing_matrix_rejects_non_normalized_columns():
    S = np.array([[0.9, 0.2], [0.2, 0.9]], dtype=float)  # col sums = 1.1, 1.1
    with pytest.raises(ValueError, match="columns must sum to 1"):
        validate_physical_smearing(S)
