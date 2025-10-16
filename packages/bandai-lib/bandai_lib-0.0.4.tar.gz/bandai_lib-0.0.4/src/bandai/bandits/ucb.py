import torch
from jaxtyping import Float
from torch import Tensor

from bandai.utils import batched_quadratic_form

from .protocols import ArmDist, Context, ContextualMAB, Rewards

ArmMat = Float[Tensor, " A D D"]
ArmVec = Float[Tensor, " A D"]


class DisjointLinUCB(ContextualMAB):
    """
    DisjointLinUCB.
    """

    def __init__(
        self,
        n_arms: int,
        ctx_dim: int,
        exploration_coef: float = 1.0,
    ) -> None:
        self._alpha = exploration_coef

        self._cov_mat: ArmMat = torch.eye(ctx_dim).repeat(n_arms, 1, 1)
        self._inv_cov: ArmMat = torch.eye(ctx_dim).repeat(n_arms, 1, 1)
        self._bias: ArmVec = torch.zeros(n_arms, ctx_dim)
        self._estim: ArmVec = torch.zeros(n_arms, ctx_dim)

    def update(self, arm: int, ctx: Context, rwd: Rewards) -> None:
        # update A = A + X'X
        self._cov_mat[arm] += ctx.T @ ctx

        # update b = b + X'r
        self._bias[arm] += ctx.T @ rwd

        # recompute inv(A)
        self._inv_cov[arm] = torch.linalg.inv(self._cov_mat[arm])  # type: ignore

        # update estimate \theta = inv(A) @ b
        self._estim[arm] = self._inv_cov[arm] @ self._bias[arm]

    def predict(self, ctx: Context) -> ArmDist:
        # compute mean estimtate x'\theta
        mean = ctx @ self._estim.T

        # compute upper confidence bound sqrt(x'Ax)
        var = batched_quadratic_form(ctx, self._inv_cov)

        # return final UCB scores
        return mean + self._alpha * var.sqrt()
