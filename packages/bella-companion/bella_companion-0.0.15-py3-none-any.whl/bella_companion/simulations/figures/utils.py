from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns


def _set_time_bin_xticks(n: int, reverse: bool = False):
    xticks_labels = range(n)
    if reverse:
        xticks_labels = reversed(xticks_labels)
    plt.xticks(ticks=range(n), labels=list(map(str, xticks_labels)))  # pyright: ignore
    plt.xlabel("Time bin")  # pyright: ignore


def step(
    x: list[float],
    reverse_xticks: bool = False,
    label: str | None = None,
    color: str | None = None,
    linestyle: str | None = None,
):
    x = [x[0], *x]
    n = len(x)
    plt.step(  # pyright: ignore
        list(range(n)), x, label=label, color=color, linestyle=linestyle
    )
    _set_time_bin_xticks(n, reverse_xticks)


def _count_time_bins(true_values: dict[str, list[float]]) -> int:
    assert (
        len({len(true_value) for true_value in true_values.values()}) == 1
    ), "All targets must have the same number of change times."
    return len(next(iter((true_values.values()))))


def plot_maes_per_time_bin(
    logs_summaries: dict[str, pl.DataFrame],
    true_values: dict[str, list[float]],
    output_filepath: str | Path,
    reverse_xticks: bool = False,
):
    def _mae(target: str, i: int) -> pl.Expr:
        return (pl.col(f"{target}i{i}_median") - true_values[target][i]).abs()

    n_time_bins = _count_time_bins(true_values)
    df = pl.concat(
        logs_summaries[model]
        .select(
            pl.mean_horizontal([_mae(target, i) for target in true_values]).alias("MAE")
        )
        .with_columns(pl.lit(i).alias("Time bin"), pl.lit(model).alias("Model"))
        for i in range(n_time_bins)
        for model in logs_summaries
    )
    sns.violinplot(
        x="Time bin",
        y="MAE",
        hue="Model",
        data=df,
        inner=None,
        cut=0,
        density_norm="width",
        legend=False,
    )
    _set_time_bin_xticks(n_time_bins, reverse_xticks)
    plt.savefig(output_filepath)  # pyright: ignore
    plt.close()


def plot_coverage_per_time_bin(
    logs_summaries: dict[str, pl.DataFrame],
    true_values: dict[str, list[float]],
    output_filepath: str | Path,
    reverse_xticks: bool = False,
):
    def _coverage(model: str, target: str, i: int) -> float:
        lower_bound = logs_summaries[model][f"{target}i{i}_lower"]
        upper_bound = logs_summaries[model][f"{target}i{i}_upper"]
        true_value = true_values[target][i]
        N = len(logs_summaries[model])
        return ((lower_bound <= true_value) & (true_value <= upper_bound)).sum() / N

    n_time_bins = _count_time_bins(true_values)
    for model in logs_summaries:
        avg_coverage_by_time_bin = [
            np.mean([_coverage(model, target, i) for target in true_values])
            for i in range(_count_time_bins(true_values))
        ]
        plt.plot(avg_coverage_by_time_bin, marker="o")  # pyright: ignore

    _set_time_bin_xticks(n_time_bins, reverse_xticks)
    plt.ylabel("Coverage")  # pyright: ignore
    plt.ylim((0, 1.05))  # pyright: ignore
    plt.savefig(output_filepath)  # pyright: ignore
    plt.close()
