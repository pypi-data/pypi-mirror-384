import os
from pathlib import Path

import joblib
import polars as pl

from bella_companion.utils import read_weights_dir, summarize_logs_dir


def summarize_logs():
    data_dir = Path(__file__).parent / "data"
    change_times = pl.read_csv(data_dir / "change_times.csv", has_header=False)
    n_time_bins = len(change_times) + 1

    logs_dir = Path(os.environ["BELLA_BEAST_OUTPUT_DIR"]) / "fbd-empirical"
    summaries = summarize_logs_dir(
        logs_dir=logs_dir,
        target_columns=[
            f"{rate}RateSPi{i}_{t}"
            for rate in ["birth", "death"]
            for i in range(n_time_bins)
            for t in ["0", "1", "2", "3"]
        ],
    )
    weights = read_weights_dir(logs_dir)

    summaries_dir = Path(os.environ["BELLA_LOG_SUMMARIES_DIR"], "fbd-empirical")
    os.makedirs(summaries_dir, exist_ok=True)
    summaries.write_csv(summaries_dir / "MLP.csv")
    joblib.dump(weights, summaries_dir / "MLP.weights.pkl")
