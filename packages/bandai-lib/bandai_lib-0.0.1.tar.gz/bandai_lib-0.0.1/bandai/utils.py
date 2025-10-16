import torch
from jaxtyping import Float
from torch import Tensor


def batched_quadratic_form(
    batch_vec: Float[Tensor, " B D"],
    batch_mat: Float[Tensor, " A D D"],
) -> Float[Tensor, " B A"]:
    """
    Computes batched quadratic form action.
    """
    return torch.einsum("bd, acd, bc -> ba", batch_vec, batch_mat, batch_vec)
