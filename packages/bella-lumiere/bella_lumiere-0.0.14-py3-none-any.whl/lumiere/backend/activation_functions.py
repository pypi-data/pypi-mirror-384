import numpy as np
from numpy.typing import ArrayLike

from lumiere.typing import Array


def sigmoid(
    x: ArrayLike,
    lower: float = 0.0,
    upper: float = 1.0,
    shape: float = 1.0,
) -> Array:
    x = np.asarray(x, dtype=np.float64)
    return lower + (upper - lower) / (1 + np.exp(-shape * x))


def relu(x: ArrayLike) -> Array:
    return np.maximum(0, x)


def softplus(x: ArrayLike) -> Array:
    return np.log1p(np.exp(x))


def tanh(x: ArrayLike) -> Array:
    return np.tanh(x)
