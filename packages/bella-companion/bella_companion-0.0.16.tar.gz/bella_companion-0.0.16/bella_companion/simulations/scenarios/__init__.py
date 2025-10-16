from bella_companion.simulations.scenarios.epi_multitype import SCENARIO as EPI_MULTITYPE_SCENARIO
from bella_companion.simulations.scenarios.epi_skyline import SCENARIOS as EPI_SKYLINE_SCENARIOS
from bella_companion.simulations.scenarios.fbd_2traits import SCENARIO as FBD_2TRAITS_SCENARIO
from bella_companion.simulations.scenarios.fbd_no_traits import SCENARIOS as FBD_NO_TRAITS_SCENARIOS
from bella_companion.simulations.scenarios.scenario import Scenario, ScenarioType

SCENARIOS = {
    **{
        f"epi-skyline_{i}": scenario
        for i, scenario in enumerate(EPI_SKYLINE_SCENARIOS, start=1)
    },
    "epi-multitype": EPI_MULTITYPE_SCENARIO,
    **{
        f"fbd-no-traits_{i}": scenario
        for i, scenario in enumerate(FBD_NO_TRAITS_SCENARIOS, start=1)
    },
    "fbd-2traits": FBD_2TRAITS_SCENARIO,
}

__all__ = ["SCENARIOS", "Scenario", "ScenarioType"]
