import json
import os
from glob import glob
from pathlib import Path

import numpy as np
import polars as pl

from bella_companion.simulations.scenarios import SCENARIOS


def _mae(summary: pl.DataFrame, true_values: dict[str, float]) -> float:
    preds = [float(np.median(summary[f"{target}_median"])) for target in true_values]
    targets = list(true_values.values())
    return float(np.mean([np.abs(np.array(preds) - np.array(targets))]))


def _coverage(summary: pl.DataFrame, true_values: dict[str, float]) -> float:
    coverages = [
        (
            (summary[f"{target}_lower"] <= true_values[target])
            & (true_values[target] <= summary[f"{target}_upper"])
        ).sum()
        / len(summary)
        for target in true_values
    ]
    return float(np.mean(coverages))


def _avg_ci_width(summary: pl.DataFrame, true_values: dict[str, float]) -> float:
    widths = [
        np.median(summary[f"{target}_upper"] - summary[f"{target}_lower"])
        for target in true_values
    ]
    return float(np.mean(widths))


def print_metrics():
    metrics = {}
    for name, scenario in SCENARIOS.items():
        summaries_dir = Path(os.environ["BELLA_LOG_SUMMARIES_DIR"]) / name
        summaries = {
            Path(log_summary).stem: pl.read_csv(log_summary)
            for log_summary in glob(str(summaries_dir / "*.csv"))
        }
        metrics[name] = {
            target: {
                model: {
                    "MAE": _mae(summary, true_values),
                    "coverage": _coverage(summary, true_values),
                    "avg_CI_width": _avg_ci_width(summary, true_values),
                }
                for model, summary in summaries.items()
            }
            for target, true_values in scenario.targets.items()
        }
    with open("simulation-metrics.json", "w") as f:
        json.dump(metrics, f)
