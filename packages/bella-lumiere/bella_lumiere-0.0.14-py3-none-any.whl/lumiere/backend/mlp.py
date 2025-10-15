from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike

from lumiere.typing import ActivationFunction, Array, Weights


def forward(
    weights: Weights,
    inputs: ArrayLike,  # shape: (n_samples, n_features)
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
) -> Array:  # shape: (n_samples,)
    x = np.asarray(inputs, dtype=np.float64)
    n_samples, _ = x.shape
    activation_funcs = [hidden_activation] * (len(weights) - 1) + [output_activation]
    for layer_weights, activation_func in zip(weights, activation_funcs):
        bias = np.ones((n_samples, 1))
        x = np.hstack((bias, x))
        x = np.dot(x, layer_weights)
        x = activation_func(x)
    return x.flatten()


def get_effective_prior(
    features_grid: ArrayLike,  # shape: (n_feature_combinations, n_features)
    hidden_neurons: Sequence[int],
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
    n_draws: int = 1_000,
) -> list[float]:
    _, n_features = np.asarray(features_grid, dtype=np.float64).shape
    topology = [n_features, *hidden_neurons, 1]
    prior: list[float] = []
    for _ in range(n_draws):
        weights = [
            np.random.normal(size=(n_inputs + 1, n_outputs))
            for n_inputs, n_outputs in zip(topology, topology[1:])
        ]
        prior.extend(
            forward(
                weights=weights,
                inputs=features_grid,
                hidden_activation=hidden_activation,
                output_activation=output_activation,
            ).tolist()
        )
    return prior
