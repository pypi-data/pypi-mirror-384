import os
from pathlib import Path

from phylogenie import generate_trees

from bella_companion.simulations.scenarios import SCENARIOS, ScenarioType

N_TREES = 100
MIN_TIPS = 200
MAX_TIPS = 500


def generate_data():
    base_output_dir = Path(os.environ["BELLA_SIMULATIONS_DATA_DIR"])
    for scenario_name, scenario in SCENARIOS.items():
        generate_trees(
            output_dir=base_output_dir / scenario_name,
            n_trees=N_TREES,
            events=scenario.events,
            init_state=scenario.init_state,
            sampling_probability_at_present=int(scenario.type == ScenarioType.FBD),
            max_time=scenario.max_time,
            seed=42,
            acceptance_criterion=lambda t: MIN_TIPS
            <= sum(1 for l in t.get_leaves() if l.branch_length > 0)  # pyright: ignore
            <= MAX_TIPS,
        )
