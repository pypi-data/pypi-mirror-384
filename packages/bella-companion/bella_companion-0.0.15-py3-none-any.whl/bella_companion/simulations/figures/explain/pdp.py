import os
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from joblib import Parallel, delayed
from lumiere.typing import ActivationFunction, Weights
from tqdm import tqdm

from bella_companion.simulations.features import Feature
from bella_companion.utils import get_median_partial_dependence_values


def plot_partial_dependencies(
    weights: list[list[Weights]],  # shape: (n_runs, n_weights_samples, ...)
    features: dict[str, Feature],
    output_dir: Path,
    hidden_activation: ActivationFunction,
    output_activation: ActivationFunction,
):
    os.makedirs(output_dir, exist_ok=True)

    continuous_grid: list[float] = np.linspace(0, 1, 10).tolist()
    features_grid: list[list[float]] = [
        [0, 1] if feature.is_binary else continuous_grid
        for feature in features.values()
    ]
    jobs = Parallel(n_jobs=-1, return_as="generator_unordered")(
        delayed(
            partial(
                get_median_partial_dependence_values,
                features_grid=features_grid,
                hidden_activation=hidden_activation,
                output_activation=output_activation,
            )
        )(w)
        for w in weights
    )
    pdvalues = [
        job for job in tqdm(jobs, total=len(weights), desc="Evaluating PDPs")
    ]  # shape: (n_runs, n_features, n_grid_points)
    pdvalues = [
        np.array(mcmc_pds).T for mcmc_pds in zip(*pdvalues)
    ]  # shape: (n_features, n_grid_points, n_runs)

    if any(not f.is_binary for f in features.values()):
        for (label, feature), feature_pdvalues in zip(features.items(), pdvalues):
            if not feature.is_binary:
                color = "#E74C3C" if feature.is_relevant else "gray"
                median = np.median(feature_pdvalues, axis=1)
                lower = np.percentile(feature_pdvalues, 2.5, axis=1)
                high = np.percentile(feature_pdvalues, 100 - 2.5, axis=1)
                plt.fill_between(  # pyright: ignore
                    continuous_grid, lower, high, alpha=0.25, color=color
                )
                for mcmc_pds in feature_pdvalues.T:
                    plt.plot(  # pyright: ignore
                        continuous_grid, mcmc_pds, color=color, alpha=0.2, linewidth=1
                    )
                plt.plot(  # pyright: ignore
                    continuous_grid, median, color=color, label=label
                )
        plt.xlabel("Feature value")  # pyright: ignore
        plt.ylabel("MLP Output")  # pyright: ignore
        plt.legend()  # pyright: ignore
        plt.savefig(output_dir / "PDPs-continuous.svg")  # pyright: ignore
        plt.close()

    if any(f.is_binary for f in features.values()):
        data: list[float] = []
        grid: list[int] = []
        labels: list[str] = []
        for (label, feature), feature_pdvalues in zip(features.items(), pdvalues):
            if feature.is_binary:
                for i in [0, 1]:
                    data.extend(feature_pdvalues[i])
                    grid.extend([i] * len(feature_pdvalues[i]))
                    labels.extend([label] * len(feature_pdvalues[i]))

        ax = sns.violinplot(
            x=labels, y=data, hue=grid, split=True, cut=0, inner="quartile"
        )
        ax.get_legend().remove()  # pyright: ignore

        for i, f in enumerate([f for f in features.values() if f.is_binary]):
            color = "#E74C3C" if f.is_relevant else "gray"
            for coll in ax.collections[i * 2 : i * 2 + 2]:
                coll.set_facecolor(color)

        plt.xlabel("Feature")  # pyright: ignore
        plt.ylabel("MLP Output")  # pyright: ignore
        plt.savefig(output_dir / "PDPs-categorical.svg")  # pyright: ignore
        plt.close()
