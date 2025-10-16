from typing import Literal

import torch
from torch import nn


def convert_ids_to_logits(ids: torch.Tensor, d: Literal[1, 2, 3], num_classes: int) -> torch.Tensor:
    if ids.dtype != torch.int or ids.min() < 0:
        raise TypeError("`ids` should be positive integers")
    d += 1
    if ids.ndim != d:
        if ids.ndim == d + 1 and ids.shape[1] == 1:
            ids = ids.squeeze(1)
        else:
            raise ValueError(f"`ids` should be {d} dimensional or {d + 1} dimensional with single channel")
    return nn.functional.one_hot(ids.long(), num_classes).movedim(-1, 1).float()


def convert_logits_to_ids(logits: torch.Tensor, *, channel_dim: int = 1) -> torch.Tensor:
    return logits.max(channel_dim).indices.int()
