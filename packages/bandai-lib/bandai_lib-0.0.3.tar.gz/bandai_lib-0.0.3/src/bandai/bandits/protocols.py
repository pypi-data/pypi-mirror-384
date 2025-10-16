from typing import Protocol

from jaxtyping import Float
from torch import Tensor

ArmDist = Float[Tensor, " B A"]
Context = Float[Tensor, " B D"]
Rewards = Float[Tensor, " B"]


class ContextualMAB(Protocol):
    """
    Contextual Multi-Armed Bandit Protocol.
    """

    def update(self, arm: int, ctx: Context, rwd: Rewards) -> None: ...

    def predict(self, ctx: Context) -> ArmDist: ...
