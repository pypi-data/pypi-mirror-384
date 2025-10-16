import numpy as np
from numpy.random import Generator
from phylogenie import SkylineVector, get_canonical_events

from bella_companion.simulations.features import Feature
from bella_companion.simulations.scenarios.common import (
    FBD_MAX_TIME,
    FBD_RATE_UPPER,
    FBD_SAMPLING_RATE,
    get_prior_params,
    get_random_time_series_predictor,
    get_start_type_prior_probabilities,
)
from bella_companion.simulations.scenarios.scenario import Scenario, ScenarioType


def _get_random_predictor(rng: Generator) -> list[float]:
    return np.repeat(
        get_random_time_series_predictor(rng, N_TIME_BINS), N_STATES
    ).tolist()


STATES = ["00", "01", "10", "11"]
_INIT_STATE = "00"
N_STATES = len(STATES)
N_TIME_BINS = 10
_CHANGE_TIMES = np.linspace(0, FBD_MAX_TIME, N_TIME_BINS + 1)[1:-1].tolist()
BIRTH_RATE_TRAIT1_UNSET = np.linspace(0.6, 0.1, N_TIME_BINS).tolist()
BIRTH_RATE_TRAIT1_SET = np.linspace(0.3, 0.05, N_TIME_BINS).tolist()
DEATH_RATE_TRAIT1_UNSET = np.linspace(0.1, 0.4, N_TIME_BINS).tolist()
DEATH_RATE_TRAIT1_SET = np.linspace(0.1, 0.2, N_TIME_BINS).tolist()
BIRTH_RATES = {
    "00": BIRTH_RATE_TRAIT1_UNSET,
    "01": BIRTH_RATE_TRAIT1_UNSET,
    "10": BIRTH_RATE_TRAIT1_SET,
    "11": BIRTH_RATE_TRAIT1_SET,
}
DEATH_RATES = {
    "00": DEATH_RATE_TRAIT1_UNSET,
    "01": DEATH_RATE_TRAIT1_UNSET,
    "10": DEATH_RATE_TRAIT1_SET,
    "11": DEATH_RATE_TRAIT1_SET,
}
RATES = {"birth": BIRTH_RATES, "death": DEATH_RATES}
_MIGRATION_RATES = (
    np.array([[1, 1, 0], [1, 0, 1], [1, 0, 1], [0, 1, 1]]) * 0.1
).tolist()

SCENARIO = Scenario(
    type=ScenarioType.FBD,
    max_time=FBD_MAX_TIME,
    init_state=_INIT_STATE,
    events=get_canonical_events(
        states=STATES,
        sampling_rates=FBD_SAMPLING_RATE,
        remove_after_sampling=False,
        birth_rates=SkylineVector(
            value=list(zip(*BIRTH_RATES.values())), change_times=_CHANGE_TIMES
        ),
        death_rates=SkylineVector(
            value=list(zip(*DEATH_RATES.values())), change_times=_CHANGE_TIMES
        ),
        migration_rates=_MIGRATION_RATES,
    ),
    get_random_predictor=_get_random_predictor,
    beast_args={
        "types": ",".join(STATES),
        "startTypePriorProbs": get_start_type_prior_probabilities(STATES, _INIT_STATE),
        "processLength": FBD_MAX_TIME,
        "changeTimes": " ".join(map(str, _CHANGE_TIMES)),
        **get_prior_params("birthRate", FBD_RATE_UPPER, N_TIME_BINS * N_STATES),
        **get_prior_params("deathRate", FBD_RATE_UPPER, N_TIME_BINS * N_STATES),
        "samplingRate": FBD_SAMPLING_RATE,
        "migrationRate": " ".join(map(str, np.array(_MIGRATION_RATES).flatten())),
        "timePredictor": " ".join(
            list(map(str, np.repeat(np.linspace(0, 1, N_TIME_BINS), N_STATES)))
        ),
        "trait1Predictor": " ".join(map(str, [1, 1, 0, 0] * N_TIME_BINS)),
        "trait2Predictor": " ".join(map(str, [0, 1, 0, 1] * N_TIME_BINS)),
    },
    targets={
        f"{rate}Rate": {
            f"{rate}RateSPi{i}_{s}": values[s][i]
            for i in range(N_TIME_BINS)
            for s in STATES
        }
        for rate, values in RATES.items()
    },
    features={
        f"{rate}Rate": {
            "timePredictor": Feature(is_binary=False, is_relevant=True),
            "trait1Predictor": Feature(is_binary=True, is_relevant=True),
            "trait2Predictor": Feature(is_binary=True, is_relevant=False),
            "randomPredictor": Feature(is_binary=False, is_relevant=False),
        }
        for rate in RATES
    },
)
