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
from bella_companion.simulations.scenarios.epi_skyline import REPRODUCTION_NUMBERS


def plot_epi_skyline_results():
    output_dir = Path(os.environ["BELLA_FIGURES_DIR"]) / "epi-skyline-results"
    os.makedirs(output_dir, exist_ok=True)

    for i, reproduction_number in enumerate(REPRODUCTION_NUMBERS, start=1):
        summaries_dir = Path(os.environ["BELLA_LOG_SUMMARIES_DIR"]) / f"epi-skyline_{i}"
        logs_summaries = {
            "Nonparametric": pl.read_csv(summaries_dir / "Nonparametric.csv"),
            "GLM": pl.read_csv(summaries_dir / "GLM.csv"),
            "MLP": pl.read_csv(summaries_dir / "MLP-16_8.csv"),
        }
        true_values = {"reproductionNumberSP": reproduction_number}

        for log_summary in logs_summaries.values():
            step(
                [
                    float(np.median(log_summary[f"reproductionNumberSPi{i}_median"]))
                    for i in range(len(reproduction_number))
                ]
            )
        step(reproduction_number, color="k", linestyle="--")
        plt.ylabel("Reproduction number")  # pyright: ignore
        plt.savefig(output_dir / f"predictions-{i}.svg")  # pyright: ignore
        plt.close()

        plot_coverage_per_time_bin(
            logs_summaries, true_values, output_dir / f"coverage-{i}.svg"
        )
        plot_maes_per_time_bin(
            logs_summaries, true_values, output_dir / f"maes-{i}.svg"
        )
