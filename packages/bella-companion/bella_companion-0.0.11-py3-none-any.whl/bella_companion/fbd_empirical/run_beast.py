import json
import os
from itertools import combinations
from pathlib import Path

import numpy as np
import polars as pl
from phylogenie import load_newick
from phylogenie.utils import get_node_depths
from tqdm import tqdm

from bella_companion.utils import submit_job


def _get_migration_rates_init(types: list[str], init_rate: float = 1) -> str:
    mus: list[float] = []
    for t1, t2 in combinations(types, 2):
        traits1 = np.array(list(map(int, t1.split("_"))))
        traits2 = np.array(list(map(int, t2.split("_"))))
        mus.append(init_rate if np.sum(np.abs(traits1 - traits2)) == 1 else 0)
    return " ".join(map(str, mus))


def run_beast():
    from dotenv import load_dotenv

    load_dotenv()
    base_output_dir = Path(os.environ["BELLA_BEAST_OUTPUT_DIR"])
    output_dir = base_output_dir / "fbd-empirical"
    os.makedirs(output_dir, exist_ok=True)

    data_dir = Path(__file__).parent / "data"
    tree_file = data_dir / "trees.nwk"
    change_times_file = data_dir / "change_times.csv"
    traits_file = data_dir / "traits.csv"

    trees = load_newick(str(tree_file))
    assert isinstance(trees, list)

    traits = pl.read_csv(traits_file, separator="\t", null_values=["NA"])

    change_times = (
        pl.read_csv(change_times_file, has_header=False).to_series().to_numpy()
    )

    types: list[str] = sorted(traits["type"].unique())
    types.remove("?")
    N = len(types)

    time_predictor = " ".join(list(map(str, np.repeat([0, *change_times], N))))
    log10BM_predictor = " ".join(
        [t.split("_")[0] for t in types] * (len(change_times) + 1)
    )
    midlat_predictor = " ".join(
        [t.split("_")[1] for t in types] * (len(change_times) + 1)
    )

    job_ids = {}
    for i, tree in enumerate(tqdm(trees)):
        process_length = max(get_node_depths(tree).values())
        command = " ".join(
            [
                os.environ["BELLA_RUN_BEAST_CMD"],
                f'-D types="{",".join(types)}"',
                f'-D startTypePriorProbs="{" ".join([str(1/N)] * N)}"',
                f"-D birthRateUpper=5",
                f"-D deathRateUpper=5",
                f"-D samplingRateUpper=5",
                f'-D samplingRateInit="{" ".join(["2.5"] * N)}"',
                f"-D migrationRateUpper=5",
                f'-D migrationRateInit="{_get_migration_rates_init(types, 2.5)}"',
                f'-D nodes="16 8"',
                f'-D layersRange="0,1,2"',
                f"-D tree_file={tree_file}",
                f"-D treeIndex={i}",
                f"-D changeTimesFile={change_times_file}",
                f"-D traitsFile={traits_file}",
                f"-D processLength={process_length}",
                f'-D timePredictor="{time_predictor}"',
                f'-D log10BM_predictor="{log10BM_predictor}"',
                f'-D midlat_predictor="{midlat_predictor}"',
                f"-prefix {output_dir}{os.sep}",
                str(Path(os.environ["BELLA_BEAST_CONFIGS_DIR"]) / "fbd-empirical.xml"),
            ]
        )
        job_ids[i] = submit_job(
            command,
            Path(os.environ["BELLA_SBATCH_LOG_DIR"]) / "fbd-empirical" / str(i),
            mem_per_cpu="12000",
        )

    with open(base_output_dir / "fbd_empirical_job_ids.json", "w") as f:
        json.dump(job_ids, f)
