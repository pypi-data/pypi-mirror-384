from typing import Any

import numpy as np
from numpy.random import Generator

EPI_MAX_TIME = 250
EPI_SAMPLING_PROPORTION = 0.15
BECOME_UNINFECTIOUS_RATE = 0.07

FBD_MAX_TIME = 35
FBD_SAMPLING_RATE = 0.2
FBD_RATE_UPPER = 2


def get_start_type_prior_probabilities(types: list[str], init_type: str):
    start_type_prior_probabilities = ["0"] * len(types)
    start_type_prior_probabilities[types.index(init_type)] = "1"
    return " ".join(start_type_prior_probabilities)


def get_random_time_series_predictor(rng: Generator, n_time_bins: int) -> list[float]:
    return np.cumsum(rng.normal(size=n_time_bins)).tolist()


def get_prior_params(target: str, upper: float, n: int) -> dict[str, Any]:
    return {
        f"{target}Upper": upper,
        f"{target}Init": " ".join([str(upper / 2)] * n),
    }
