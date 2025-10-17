import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from bella_companion.simulations.figures.utils import (
    plot_coverage_per_time_bin,
    plot_maes_per_time_bin,
    step,
)
from bella_companion.simulations.scenarios.fbd_no_traits import RATES


def plot_fbd_no_traits_results():
    output_dir = Path(os.environ["BELLA_FIGURES_DIR"]) / "fbd-no-traits-predictions"
    os.makedirs(output_dir, exist_ok=True)

    for i, rates in enumerate(RATES, start=1):
        summaries_dir = (
            Path(os.environ["BELLA_LOG_SUMMARIES_DIR"]) / f"fbd-no-traits_{i}"
        )
        logs_summaries = {
            "Nonparametric": pl.read_csv(summaries_dir / "Nonparametric.csv"),
            "GLM": pl.read_csv(summaries_dir / "GLM.csv"),
            "MLP": pl.read_csv(summaries_dir / "MLP-16_8.csv"),
        }
        true_values = {"birthRateSP": rates["birth"], "deathRateSP": rates["death"]}

        for id, rate in true_values.items():
            for log_summary in logs_summaries.values():
                step(
                    [
                        float(np.median(log_summary[f"{id}i{i}_median"]))
                        for i in range(len(rate))
                    ],
                    reverse_xticks=True,
                )
            step(rate, color="k", linestyle="--", reverse_xticks=True)
            plt.ylabel(  # pyright: ignore
                r"$\lambda$" if id == "birthRateSP" else r"$\mu$"
            )
            plt.savefig(output_dir / f"{id}-predictions-{i}-.svg")  # pyright: ignore
            plt.close()

        plot_coverage_per_time_bin(
            logs_summaries,
            true_values,
            output_dir / f"coverage-{i}.svg",
            reverse_xticks=True,
        )
        plot_maes_per_time_bin(
            logs_summaries,
            true_values,
            output_dir / f"maes-{i}.svg",
            reverse_xticks=True,
        )
