from collections.abc import Sequence
from itertools import product

import numpy as np

from lumiere.backend import mlp
from lumiere.backend.activation_functions import sigmoid
from lumiere.typing import ActivationFunction, Weights


def get_partial_dependence_values(
    weights: Weights,
    features_grid: Sequence[Sequence[float]],
    hidden_activation: ActivationFunction = sigmoid,
    output_activation: ActivationFunction = sigmoid,
) -> list[list[float]]:  # shape: (n_features, n_grid_points)
    inputs = np.array(list(product(*features_grid)), dtype=np.float64)
    pdvalues: list[list[float]] = []
    for feature_idx in range(len(features_grid)):
        feature_pdvalues: list[float] = []
        for feature_value in features_grid[feature_idx]:
            x = np.copy(inputs)
            x[:, feature_idx] = feature_value
            mean_output = np.mean(
                mlp.forward(weights, x, hidden_activation, output_activation)
            )
            feature_pdvalues.append(float(mean_output))
        pdvalues.append(feature_pdvalues)
    return pdvalues
