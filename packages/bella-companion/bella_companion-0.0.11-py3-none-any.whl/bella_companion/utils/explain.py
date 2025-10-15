import numpy as np
from lumiere import get_partial_dependence_values, get_shap_features_importance
from lumiere.typing import ActivationFunction, Weights
from numpy.typing import ArrayLike


def get_median_partial_dependence_values(
    weights: list[Weights],  # shape: (n_weight_samples, ...)
    features_grid: list[list[float]],
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
) -> list[list[float]]:  # shape: (n_features, n_grid_points)
    pdvalues = [
        get_partial_dependence_values(
            weights=w,
            features_grid=features_grid,
            hidden_activation=hidden_activation,
            output_activation=output_activation,
        )
        for w in weights
    ]
    return [
        np.median([pd[feature_idx] for pd in pdvalues], axis=0).tolist()
        for feature_idx in range(len(features_grid))
    ]


def get_median_shap_features_importance(
    weights: list[Weights],
    inputs: ArrayLike,
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
) -> list[float]:  # length: n_features
    features_importance = np.array(
        [
            get_shap_features_importance(
                weights=w,
                inputs=inputs,
                hidden_activation=hidden_activation,
                output_activation=output_activation,
            )
            for w in weights
        ]
    )
    return np.median(features_importance, axis=0).tolist()
