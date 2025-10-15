from functools import partial

import numpy as np
from phylogenie import SkylineParameter, get_canonical_events

from bella_companion.simulations.features import Feature
from bella_companion.simulations.scenarios.common import (
    FBD_MAX_TIME,
    FBD_RATE_UPPER,
    FBD_SAMPLING_RATE,
    get_prior_params,
    get_random_time_series_predictor,
)
from bella_companion.simulations.scenarios.scenario import Scenario, ScenarioType


def _get_scenario(rates: dict[str, list[float]]) -> Scenario:
    if len(rates["birth"]) != len(rates["death"]):
        raise ValueError("Birth rate and death rate lists must have the same length.")
    n_time_bins = len(rates["birth"])
    change_times = np.linspace(0, FBD_MAX_TIME, n_time_bins + 1)[1:-1].tolist()

    return Scenario(
        type=ScenarioType.FBD,
        max_time=FBD_MAX_TIME,
        events=get_canonical_events(
            states=["X"],
            sampling_rates=FBD_SAMPLING_RATE,
            remove_after_sampling=False,
            birth_rates=SkylineParameter(rates["birth"], change_times),
            death_rates=SkylineParameter(rates["death"], change_times),
        ),
        get_random_predictor=partial(
            get_random_time_series_predictor, n_time_bins=n_time_bins
        ),
        beast_args={
            "processLength": FBD_MAX_TIME,
            "changeTimes": " ".join(map(str, change_times)),
            **get_prior_params("birthRate", FBD_RATE_UPPER, n_time_bins),
            **get_prior_params("deathRate", FBD_RATE_UPPER, n_time_bins),
            "samplingRate": FBD_SAMPLING_RATE,
            "timePredictor": " ".join(map(str, np.linspace(0, 1, n_time_bins))),
        },
        targets={
            f"{rate}Rate": {f"{rate}RateSPi{i}": values[i] for i in range(n_time_bins)}
            for rate, values in rates.items()
        },
        features={
            f"{rate}Rate": {
                "timePredictor": Feature(
                    is_binary=False, is_relevant=len(set(values)) > 1
                ),
                "randomPredictor": Feature(is_binary=False, is_relevant=False),
            }
            for rate, values in rates.items()
        },
    )


RATES = [
    {"birth": [0.2] * 10, "death": [0.1] * 10},
    {
        "birth": np.linspace(0.4, 0.1, 10).tolist(),
        "death": np.linspace(0.1, 0.2, 10).tolist(),
    },
    {
        "birth": [0.4] * 5 + [0.1] * 3 + [0.01] * 2,
        "death": [0.05] * 7 + [0.3] * 1 + [0.01] * 2,
    },
]
SCENARIOS = [_get_scenario(r) for r in RATES]
