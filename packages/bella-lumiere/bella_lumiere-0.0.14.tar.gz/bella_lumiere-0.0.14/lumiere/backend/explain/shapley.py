from functools import partial

import numpy as np
import shap  # pyright: ignore
from numpy.typing import ArrayLike

from lumiere.backend import mlp
from lumiere.backend.activation_functions import sigmoid
from lumiere.typing import ActivationFunction, Weights


def get_shap_features_importance(
    weights: Weights,
    inputs: ArrayLike,
    hidden_activation: ActivationFunction = sigmoid,
    output_activation: ActivationFunction = sigmoid,
) -> list[float]:  # length: n_features
    inputs = np.asarray(inputs, dtype=np.float64)
    model = partial(
        mlp.forward,
        weights,
        hidden_activation=hidden_activation,
        output_activation=output_activation,
    )
    explainer = shap.Explainer(model, inputs)
    abs_shap_values = np.abs(explainer(inputs).values)  # pyright: ignore
    return np.mean(abs_shap_values, axis=0).tolist()
