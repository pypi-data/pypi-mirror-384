import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from numpy.typing import NDArray
from phylogenie import get_node_depths, load_newick


def _plot_predictions(output_dir: Path):
    log_summaries_dir = Path(os.environ["BELLA_LOG_SUMMARIES_DIR"])
    log_summary = pl.read_csv(log_summaries_dir / "fbd-empirical" / "MLP.csv")

    data_dir = Path(__file__).parent / "data"
    change_times = (
        pl.read_csv(data_dir / "change_times.csv", has_header=False)
        .to_series()
        .to_list()
    )
    max_time = max(
        max(get_node_depths(tree).values())
        for tree in load_newick(data_dir / "trees.nwk")
    )
    time_bins = list(reversed([0.0, *change_times, max_time]))

    colors: dict[str, NDArray[np.floating]] = {
        "birth": plt.cm.Blues(np.linspace(0.4, 0.9, 4)),  # pyright: ignore
        "death": plt.cm.Oranges(np.linspace(0.4, 0.9, 4)),  # pyright: ignore
        "diversification": plt.cm.Greens(np.linspace(0.4, 0.9, 4)),  # pyright: ignore
    }
    for rate in ["birth", "death", "diversification"]:
        for type in [0, 1, 2, 3]:
            if rate == "diversification":
                estimates = log_summary.select(
                    [
                        pl.col(f"birthRateSPi{i}_{type}_median")
                        - pl.col(f"deathRateSPi{i}_{type}_median")
                        for i in range(len(change_times) + 1)
                    ]
                ).to_numpy()
            else:
                estimates = log_summary.select(
                    [
                        pl.col(f"{rate}RateSPi{i}_{type}_median")
                        for i in range(len(change_times) + 1)
                    ]
                ).to_numpy()
            median = np.median(estimates, axis=0)
            color = colors[rate][type]
            plt.step(  # pyright: ignore
                time_bins, [median[0], *median], color=color, label=type
            )

        ax = plt.gca()
        ax.invert_xaxis()
        plt.legend(title="Body mass")  # pyright: ignore
        plt.xlabel("Time (mya)")  # pyright: ignore
        plt.ylabel(  # pyright: ignore
            r"$\lambda$" if rate == "birth" else r"$\mu$" if rate == "death" else r"$d$"
        )
        plt.savefig(output_dir / f"{rate}-predictions.svg")  # pyright: ignore
        plt.close()


def plot_fbd_empirical_results():
    output_dir = Path(os.environ["BELLA_FIGURES_DIR"]) / "fbd-empirical"
    os.makedirs(output_dir, exist_ok=True)
    _plot_predictions(output_dir)
