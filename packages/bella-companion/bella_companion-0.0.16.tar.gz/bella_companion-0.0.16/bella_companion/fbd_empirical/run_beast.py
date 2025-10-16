import json
import os
from pathlib import Path

import numpy as np
import polars as pl
from phylogenie import get_node_depths, load_newick
from tqdm import tqdm

from bella_companion.utils import submit_job


def run_beast():
    base_output_dir = Path(os.environ["BELLA_BEAST_OUTPUT_DIR"])
    output_dir = base_output_dir / "fbd-empirical"
    os.makedirs(output_dir, exist_ok=True)

    data_dir = Path(__file__).parent / "data"
    tree_file = data_dir / "trees.nwk"
    change_times_file = data_dir / "change_times.csv"
    traits_file = data_dir / "traits.csv"

    trees = load_newick(str(tree_file))
    assert isinstance(trees, list)

    types = ["0", "1", "2", "3"]
    change_times = (
        pl.read_csv(change_times_file, has_header=False).to_series().to_numpy()
    )
    time_bins = [0, *change_times]
    T = len(time_bins)

    time_predictor = " ".join(list(map(str, np.repeat(time_bins, len(types)))))
    log10BM_predictor = " ".join(types * T)

    job_ids = {}
    for i, tree in enumerate(tqdm(trees)):
        process_length = max(get_node_depths(tree).values())
        command = " ".join(
            [
                os.environ["BELLA_RUN_BEAST_CMD"],
                f'-D types="{",".join(types)}"',
                f'-D startTypePriorProbs="0.25 0.25 0.25 0.25"',
                f"-D birthRateUpper=5",
                f"-D deathRateUpper=5",
                f'-D samplingChangeTimes="2.58 5.333 23.03"',
                f"-D samplingRateUpper=5",
                f'-D samplingRateInit="2.5 2.5 2.5 2.5"',
                f"-D migrationRateUpper=5",
                f'-D migrationRateInit="2.5 0 0 2.5 2.5 0 0 2.5 2.5 0 0 2.5"',
                f'-D nodes="16 8"',
                f'-D layersRange="0,1,2"',
                f"-D treeFile={tree_file}",
                f"-D treeIndex={i}",
                f"-D changeTimesFile={change_times_file}",
                f"-D traitsFile={traits_file}",
                f"-D traitValueCol=3",
                f"-D processLength={process_length}",
                f'-D timePredictor="{time_predictor}"',
                f'-D log10BMPredictor="{log10BM_predictor}"',
                f"-prefix {output_dir}{os.sep}",
                str(Path(__file__).parent / "beast_config.xml"),
            ]
        )
        job_ids[i] = submit_job(
            command,
            Path(os.environ["BELLA_SBATCH_LOG_DIR"]) / "fbd-empirical" / str(i),
            mem_per_cpu="12000",
        )

    with open(base_output_dir / "fbd_empirical_job_ids.json", "w") as f:
        json.dump(job_ids, f)
