import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from bella_companion.fbd_empirical import plot_fbd_empirical_results
from bella_companion.fbd_empirical import run_beast as run_fbd_empirical
from bella_companion.fbd_empirical import summarize_logs as summarize_fbd_empirical
from bella_companion.simulations import generate_data, generate_figures, print_metrics
from bella_companion.simulations import run_beast as run_simulations
from bella_companion.simulations import summarize_logs as summarize_simulations


def main():
    load_dotenv(Path(os.getcwd()) / ".env")

    parser = argparse.ArgumentParser(
        prog="bella",
        description="Companion tool with experiments and evaluation for Bayesian Evolutionary Layered Learning Architectures (BELLA) BEAST2 package.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "sim-data", help="Generate synthetic simulation datasets."
    ).set_defaults(func=generate_data)

    subparsers.add_parser(
        "sim-run", help="Run BEAST2 analyses on simulation datasets."
    ).set_defaults(func=run_simulations)

    subparsers.add_parser(
        "sim-summarize", help="Summarize BEAST2 log outputs for simulations."
    ).set_defaults(func=summarize_simulations)

    subparsers.add_parser(
        "sim-metrics", help="Compute and print metrics from simulation results."
    ).set_defaults(func=print_metrics)

    subparsers.add_parser(
        "sim-figures", help="Generate plots and figures from simulation results."
    ).set_defaults(func=generate_figures)

    subparsers.add_parser(
        "fbd-empirical-run", help="Run BEAST2 analyses on empirical FBD datasets."
    ).set_defaults(func=run_fbd_empirical)

    subparsers.add_parser(
        "fbd-empirical-summarize",
        help="Summarize BEAST2 log outputs for empirical FBD datasets.",
    ).set_defaults(func=summarize_fbd_empirical)

    subparsers.add_parser(
        "fbd-empirical-figures",
        help="Generate plots and figures from empirical FBD results.",
    ).set_defaults(func=plot_fbd_empirical_results)

    args = parser.parse_args()
    args.func()
