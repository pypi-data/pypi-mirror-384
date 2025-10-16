import pytest
import torch
from torch import Tensor

from bandai.utils import batched_quadratic_form


@pytest.fixture
def rand_vec_batch() -> Tensor:
    """
    Random batch of vectors.
    """
    batch, dim = 2, 3
    return torch.randn(batch, dim)


@pytest.fixture
def rand_symmat_batch() -> Tensor:
    """
    Random batch of symmetric matrices.
    """
    batch, dim = 2, 3
    mat = torch.randn(batch, dim, dim)
    return 0.5 * (mat + mat.transpose(-1, -2))  # symmetrize


def manual_quadratic_form(vec: Tensor, mat: Tensor) -> Tensor:
    """
    Compute x'Ax manually for all combinations of x from vec and A from mat.
    """
    vec_batch, mat_batch = vec.shape[0], mat.shape[0]
    result = torch.zeros(vec_batch, mat_batch)

    for i in range(vec_batch):
        for j in range(mat_batch):
            result[i, j] = vec[i] @ mat[j] @ vec[i]
    return result


def test_batched_quadratic_form(rand_vec_batch: Tensor, rand_symmat_batch: Tensor) -> None:
    expected = manual_quadratic_form(rand_vec_batch, rand_symmat_batch)
    result = batched_quadratic_form(rand_vec_batch, rand_symmat_batch)

    assert result.shape == expected.shape
    assert torch.allclose(result, expected, atol=1e-5)
