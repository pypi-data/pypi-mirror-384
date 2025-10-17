from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from numpy.random import Generator
from phylogenie.treesimulator import Event

from bella_companion.simulations.features import Feature


class ScenarioType(Enum):
    EPI = "epi"
    FBD = "fbd"


@dataclass
class Scenario:
    type: ScenarioType
    max_time: float
    events: list[Event]
    get_random_predictor: Callable[[Generator], list[float]]
    beast_args: dict[str, Any]
    targets: dict[str, dict[str, float]]
    features: dict[str, dict[str, Feature]]
    init_state: str | None = None
