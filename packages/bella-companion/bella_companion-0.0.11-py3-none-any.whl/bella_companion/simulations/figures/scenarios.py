import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bella_companion.simulations.figures.utils import step
from bella_companion.simulations.scenarios.epi_multitype import (
    MIGRATION_PREDICTOR,
    MIGRATION_RATES,
)
from bella_companion.simulations.scenarios.epi_skyline import REPRODUCTION_NUMBERS
from bella_companion.simulations.scenarios.fbd_2traits import (
    BIRTH_RATE_TRAIT1_SET,
    BIRTH_RATE_TRAIT1_UNSET,
    DEATH_RATE_TRAIT1_SET,
    DEATH_RATE_TRAIT1_UNSET,
)
from bella_companion.simulations.scenarios.fbd_no_traits import RATES


def plot_scenarios():
    output_dir = Path(os.environ["BELLA_FIGURES_DIR"]) / "scenarios"
    os.makedirs(output_dir, exist_ok=True)

    # -----------
    # epi-skyline
    # -----------
    for i, reproduction_number in enumerate(REPRODUCTION_NUMBERS, start=1):
        step(reproduction_number, color="k")
        plt.ylabel("Reproduction number")  # pyright: ignore
        plt.savefig(output_dir / f"epi-skyline_{i}.svg")  # pyright: ignore
        plt.close()

    # -------------
    # epi-multitype
    # -------------
    sort_idx = np.argsort(MIGRATION_PREDICTOR.flatten())
    plt.plot(  # pyright: ignore
        MIGRATION_PREDICTOR.flatten()[sort_idx],
        MIGRATION_RATES.flatten()[sort_idx],
        marker="o",
        color="k",
    )
    plt.xlabel("Migration predictor")  # pyright: ignore
    plt.ylabel("Migration rate")  # pyright: ignore
    plt.savefig(output_dir / "epi-multitype.svg")  # pyright: ignore
    plt.close()

    # -------------
    # fbd-no-traits
    # -------------
    for i, rates in enumerate(RATES, start=1):
        step(rates["birth"], label=r"$\lambda$", reverse_xticks=True)
        step(rates["death"], label=r"$\mu$", reverse_xticks=True)
        plt.ylabel("Rate")  # pyright: ignore
        plt.legend()  # pyright: ignore
        plt.savefig(output_dir / f"fbd-no-traits_{i}.svg")  # pyright: ignore
        plt.close()

    # -----------
    # fbd-2traits
    # -----------
    step(
        BIRTH_RATE_TRAIT1_UNSET,
        label=r"$\lambda_{0,0} = \lambda_{0,1}$",
        color="C0",
        reverse_xticks=True,
    )
    step(
        BIRTH_RATE_TRAIT1_SET,
        label=r"$\lambda_{1,0} = \lambda_{1,1}$",
        color="C0",
        linestyle="dashed",
        reverse_xticks=True,
    )
    step(
        DEATH_RATE_TRAIT1_UNSET,
        label=r"$\mu_{0,0} = \mu_{0,1}$",
        color="C1",
        reverse_xticks=True,
    )
    step(
        DEATH_RATE_TRAIT1_SET,
        label=r"$\mu_{1,0} = \mu_{1,1}$",
        color="C1",
        linestyle="dashed",
        reverse_xticks=True,
    )
    plt.ylabel("Rate")  # pyright: ignore
    plt.legend()  # pyright: ignore
    plt.savefig(output_dir / "fbd-2traits.svg")  # pyright: ignore
    plt.close()
