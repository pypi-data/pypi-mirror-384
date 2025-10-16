import os
from functools import partial
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from lumiere.backend import relu, sigmoid

from bella_companion.simulations.figures.explain import (
    plot_partial_dependencies,
    plot_shap_features_importance,
)
from bella_companion.simulations.scenarios.epi_multitype import (
    MIGRATION_PREDICTOR,
    MIGRATION_RATE_UPPER,
    MIGRATION_RATES,
    SCENARIO,
)


def _plot_predictions(log_summary: pl.DataFrame, output_dir: Path):
    targets = SCENARIO.targets["migrationRate"]
    estimates = np.array(
        [log_summary[f"{target}_median"].median() for target in targets]
    )
    lower = np.array([log_summary[f"{target}_lower"].median() for target in targets])
    upper = np.array([log_summary[f"{target}_upper"].median() for target in targets])

    sort_idx = np.argsort(MIGRATION_PREDICTOR.flatten())
    predictors = MIGRATION_PREDICTOR.flatten()[sort_idx]
    rates = MIGRATION_RATES.flatten()[sort_idx]
    estimates = estimates[sort_idx]
    lower = lower[sort_idx]
    upper = upper[sort_idx]

    plt.errorbar(  # pyright: ignore
        predictors,
        estimates,
        yerr=[estimates - lower, upper - estimates],
        fmt="o",
        color="C2",
        elinewidth=2,
        capsize=5,
    )
    plt.plot(  # pyright: ignore
        predictors, rates, linestyle="--", marker="o", color="k"
    )

    plt.xlabel("Migration predictor")  # pyright: ignore
    plt.ylabel("Migration rate")  # pyright: ignore
    plt.savefig(output_dir / "predictions.svg")  # pyright: ignore
    plt.close()


def plot_epi_multitype_results():
    output_dir = Path(os.environ["BELLA_FIGURES_DIR"]) / "epi-multitype"
    os.makedirs(output_dir, exist_ok=True)

    log_dir = Path(os.environ["BELLA_LOG_SUMMARIES_DIR"]) / "epi-multitype"
    model = "MLP-32_16"
    log_summary = pl.read_csv(log_dir / f"{model}.csv")
    weights = joblib.load(log_dir / f"{model}.weights.pkl")
    weights = [w["migrationRate"] for w in weights]

    _plot_predictions(log_summary, output_dir)
    plot_partial_dependencies(
        weights=weights,
        features=SCENARIO.features["migrationRate"],
        output_dir=output_dir,
        hidden_activation=relu,
        output_activation=partial(sigmoid, upper=MIGRATION_RATE_UPPER),
    )
    plot_shap_features_importance(
        weights=weights,
        features=SCENARIO.features["migrationRate"],
        output_file=output_dir / "shap_values.svg",
        hidden_activation=relu,
        output_activation=partial(sigmoid, upper=MIGRATION_RATE_UPPER),
    )
