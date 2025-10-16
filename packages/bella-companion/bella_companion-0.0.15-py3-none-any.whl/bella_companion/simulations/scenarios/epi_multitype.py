import numpy as np
from numpy.random import Generator
from phylogenie import get_epidemiological_events

from bella_companion.simulations.features import Feature
from bella_companion.simulations.scenarios.common import (
    BECOME_UNINFECTIOUS_RATE,
    EPI_MAX_TIME,
    EPI_SAMPLING_PROPORTION,
    get_prior_params,
    get_start_type_prior_probabilities,
)
from bella_companion.simulations.scenarios.scenario import Scenario, ScenarioType


def _get_random_predictor(rng: Generator) -> list[float]:
    return rng.uniform(-1, 1, N_TYPE_PAIRS).tolist()


TYPES = ["A", "B", "C", "D", "E"]
_REPRODUCTION_NUMBERS = [0.8, 1.0, 1.2, 1.4, 1.6]
_INIT_TYPE = "C"
N_TYPES = len(TYPES)
N_TYPE_PAIRS = N_TYPES * (N_TYPES - 1)
MIGRATION_PREDICTOR = np.random.default_rng(42).uniform(-1, 1, (N_TYPES, N_TYPES - 1))
_MIGRATION_SIGMOID_AMPLITUDE = 0.04
_MIGRATION_SIGMOID_SCALE = -8
MIGRATION_RATES = _MIGRATION_SIGMOID_AMPLITUDE / (
    1 + np.exp(_MIGRATION_SIGMOID_SCALE * MIGRATION_PREDICTOR)
)
MIGRATION_RATE_UPPER = 0.05

SCENARIO = Scenario(
    type=ScenarioType.EPI,
    max_time=EPI_MAX_TIME,
    init_state=_INIT_TYPE,
    events=get_epidemiological_events(
        states=TYPES,
        sampling_proportions=EPI_SAMPLING_PROPORTION,
        reproduction_numbers=_REPRODUCTION_NUMBERS,
        become_uninfectious_rates=BECOME_UNINFECTIOUS_RATE,
        migration_rates=MIGRATION_RATES.tolist(),
    ),
    get_random_predictor=_get_random_predictor,
    beast_args={
        "types": ",".join(TYPES),
        "startTypePriorProbs": get_start_type_prior_probabilities(TYPES, _INIT_TYPE),
        "processLength": EPI_MAX_TIME,
        **get_prior_params("migrationRate", MIGRATION_RATE_UPPER, N_TYPE_PAIRS),
        "reproductionNumber": " ".join(map(str, _REPRODUCTION_NUMBERS)),
        "becomeUninfectiousRate": BECOME_UNINFECTIOUS_RATE,
        "samplingProportion": EPI_SAMPLING_PROPORTION,
        "migrationPredictor": " ".join(map(str, MIGRATION_PREDICTOR.flatten())),
    },
    targets={
        "migrationRate": {
            f"migrationRateSP{t1}_to_{t2}": float(MIGRATION_RATES[i, j])
            for i, t1 in enumerate(TYPES)
            for j, t2 in enumerate([t for t in TYPES if t != t1])
        }
    },
    features={
        "migrationRate": {
            "migrationPredictor": Feature(is_binary=False, is_relevant=True),
            "randomPredictor": Feature(is_binary=False, is_relevant=False),
        }
    },
)
