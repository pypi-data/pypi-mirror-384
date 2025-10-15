from functools import partial
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from joblib import Parallel, delayed
from lumiere.typing import ActivationFunction, Weights
from tqdm import tqdm

from bella_companion.simulations.features import Feature
from bella_companion.utils import get_median_shap_features_importance


def plot_shap_features_importance(
    weights: list[list[Weights]],  # shape: (n_runs, n_weights_samples, ...)
    features: dict[str, Feature],
    output_file: Path,
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
):
    continuous_grid: list[float] = np.linspace(0, 1, 10).tolist()
    features_grid: list[list[float]] = [
        [0, 1] if feature.is_binary else continuous_grid
        for feature in features.values()
    ]
    inputs = list(product(*features_grid))

    jobs = Parallel(n_jobs=-1, return_as="generator_unordered")(
        delayed(
            partial(
                get_median_shap_features_importance,
                inputs=inputs,
                hidden_activation=hidden_activation,
                output_activation=output_activation,
            )
        )(w)
        for w in weights
    )
    features_importances = np.array(
        [job for job in tqdm(jobs, total=len(weights), desc="Evaluating SHAPs")]
    )  # shape: (n_runs, n_features)
    features_importances /= features_importances.sum(axis=1, keepdims=True)

    for i, (feature_name, feature) in enumerate(features.items()):
        sns.violinplot(
            y=features_importances[:, i],
            x=[feature_name] * len(features_importances),
            cut=0,
            color="#E74C3C" if feature.is_relevant else "gray",
        )
    plt.xlabel("Feature")  # pyright: ignore
    plt.ylabel("Importance")  # pyright: ignore
    plt.savefig(output_file)  # pyright: ignore
    plt.close()
