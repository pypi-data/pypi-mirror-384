from functools import partial

import numpy as np
from phylogenie import SkylineParameter, get_epidemiological_events

from bella_companion.simulations.features import Feature
from bella_companion.simulations.scenarios.common import (
    BECOME_UNINFECTIOUS_RATE,
    EPI_MAX_TIME,
    EPI_SAMPLING_PROPORTION,
    get_prior_params,
    get_random_time_series_predictor,
)
from bella_companion.simulations.scenarios.scenario import Scenario, ScenarioType


def _get_scenario(reproduction_number: list[float]) -> Scenario:
    n_time_bins = len(reproduction_number)
    change_times = np.linspace(0, EPI_MAX_TIME, n_time_bins + 1)[1:-1].tolist()
    return Scenario(
        type=ScenarioType.EPI,
        max_time=EPI_MAX_TIME,
        events=get_epidemiological_events(
            states=["X"],
            sampling_proportions=EPI_SAMPLING_PROPORTION,
            reproduction_numbers=SkylineParameter(reproduction_number, change_times),
            become_uninfectious_rates=BECOME_UNINFECTIOUS_RATE,
        ),
        get_random_predictor=partial(
            get_random_time_series_predictor, n_time_bins=n_time_bins
        ),
        beast_args={
            "processLength": EPI_MAX_TIME,
            "changeTimes": " ".join(map(str, change_times)),
            **get_prior_params(
                "reproductionNumber", REPRODUCTION_NUMBER_UPPER, n_time_bins
            ),
            "becomeUninfectiousRate": BECOME_UNINFECTIOUS_RATE,
            "samplingProportion": EPI_SAMPLING_PROPORTION,
            "timePredictor": " ".join(map(str, np.linspace(0, 1, n_time_bins))),
        },
        targets={
            "reproductionNumber": {
                f"reproductionNumberSPi{i}": r
                for i, r in enumerate(reproduction_number)
            }
        },
        features={
            "reproductionNumber": {
                "timePredictor": Feature(
                    is_binary=False, is_relevant=len(set(reproduction_number)) > 1
                ),
                "randomPredictor": Feature(is_binary=False, is_relevant=False),
            }
        },
    )


REPRODUCTION_NUMBERS: list[list[float]] = [
    [1.2] * 10,
    np.linspace(1.5, 1.0, 10).tolist(),
    np.linspace(1.2, 1.5, 5).tolist() + np.linspace(1.5, 1.0, 5).tolist(),
]
REPRODUCTION_NUMBER_UPPER = 5
SCENARIOS = [_get_scenario(r) for r in REPRODUCTION_NUMBERS]
