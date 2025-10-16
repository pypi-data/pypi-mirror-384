"""Modules that perform averaging over a history of past updates."""
from collections import deque
from collections.abc import Sequence
from typing import Any

import torch

from ...core import TensorTransform
from ...utils import tolist


class Averaging(TensorTransform):
    """Average of past ``history_size`` updates.

    Args:
        history_size (int): Number of past updates to average
        target (Target, optional): target. Defaults to 'update'.
    """
    def __init__(self, history_size: int):
        defaults = dict(history_size=history_size)
        super().__init__(defaults=defaults)

        self.add_projected_keys("grad", "history", "average")

    @torch.no_grad
    def single_tensor_apply(self, tensor, param, grad, loss, state, setting):
        history_size = setting['history_size']
        if 'history' not in state:
            state['history'] = deque(maxlen=history_size)
            state['average'] = torch.zeros_like(tensor)

        history = state['history']; average = state['average']
        if len(history) == history_size: average -= history[0]
        history.append(tensor)
        average += tensor

        return average / len(history)

class WeightedAveraging(TensorTransform):
    """Weighted average of past ``len(weights)`` updates.

    Args:
        weights (Sequence[float]): a sequence of weights from oldest to newest.
        target (Target, optional): target. Defaults to 'update'.
    """
    def __init__(self, weights: Sequence[float] | torch.Tensor | Any):
        defaults = dict(weights = tolist(weights))
        super().__init__(defaults=defaults)

        self.add_projected_keys("grad", "history")

    @torch.no_grad
    def single_tensor_apply(self, tensor, param, grad, loss, state, setting):
        weights = setting['weights']

        if 'history' not in state:
            state['history'] = deque(maxlen=len(weights))

        history = state['history']
        history.append(tensor)
        if len(history) != len(weights):
            weights = weights[-len(history):]

        average = None
        for i, (h, w) in enumerate(zip(history, weights)):
            if average is None: average = h * (w / len(history))
            else:
                if w == 0: continue
                average += h * (w / len(history))

        assert average is not None
        return average


class MedianAveraging(TensorTransform):
    """Median of past ``history_size`` updates.

    Args:
        history_size (int): Number of past updates to average
        target (Target, optional): target. Defaults to 'update'.
    """
    def __init__(self, history_size: int,):
        defaults = dict(history_size = history_size)
        super().__init__(defaults=defaults)

        self.add_projected_keys("grad", "history")

    @torch.no_grad
    def single_tensor_apply(self, tensor, param, grad, loss, state, setting):
        history_size = setting['history_size']

        if 'history' not in state:
            state['history'] = deque(maxlen=history_size)

        history = state['history']
        history.append(tensor)

        stacked = torch.stack(tuple(history), 0)
        return torch.quantile(stacked, 0.5, dim = 0)
