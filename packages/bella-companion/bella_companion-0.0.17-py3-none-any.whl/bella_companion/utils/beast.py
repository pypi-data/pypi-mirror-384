import os
from functools import partial
from glob import glob
from pathlib import Path
from typing import Any

import arviz as az
import numpy as np
import polars as pl
from joblib import Parallel, delayed
from lumiere import read_log_file, read_weights
from lumiere.typing import Weights
from tqdm import tqdm

from bella_companion.utils.slurm import get_job_metadata


def summarize_log(
    log_file: str,
    target_columns: list[str],
    burn_in: int | float = 0.1,
    hdi_prob: float = 0.95,
    job_id: str | None = None,
) -> dict[str, Any]:
    log = read_log_file(log_file, burn_in=burn_in)
    log = log.select(target_columns)
    summary: dict[str, Any] = {"id": Path(log_file).stem, "n_samples": len(log)}
    for column in log.columns:
        summary[f"{column}_median"] = log[column].median()
        summary[f"{column}_ess"] = az.ess(np.array(log[column]))  # pyright: ignore
        lower, upper = az.hdi(np.array(log[column]), hdi_prob)  # pyright: ignore
        summary[f"{column}_lower"] = lower
        summary[f"{column}_upper"] = upper
    if job_id is not None:
        summary.update(get_job_metadata(job_id))
    return summary


def summarize_logs_dir(
    logs_dir: Path,
    target_columns: list[str],
    burn_in: float = 0.1,
    hdi_prob: float = 0.95,
    job_ids: dict[str, str] | None = None,
) -> pl.DataFrame:
    os.environ["POLARS_MAX_THREADS"] = "1"
    summaries = Parallel(n_jobs=-1)(
        delayed(
            partial(
                summarize_log,
                target_columns=target_columns,
                burn_in=burn_in,
                hdi_prob=hdi_prob,
                job_id=None if job_ids is None else job_ids[Path(log_file).stem],
            )
        )(log_file)
        for log_file in tqdm(glob(str(logs_dir / "*.log")))
    )
    return pl.DataFrame(summaries)


def read_weights_dir(
    logs_dir: Path, n_samples: int = 100, burn_in: float = 0.1
) -> list[dict[str, list[Weights]]]:
    os.environ["POLARS_MAX_THREADS"] = "1"
    return Parallel(n_jobs=-1)(
        delayed(partial(read_weights, burn_in=burn_in, n_samples=n_samples))(log_file)
        for log_file in tqdm(glob(str(logs_dir / "*.log")))
    )
