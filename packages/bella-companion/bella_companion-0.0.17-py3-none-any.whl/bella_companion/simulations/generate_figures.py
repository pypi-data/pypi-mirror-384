import matplotlib.pyplot as plt

from bella_companion.simulations.figures import (
    plot_epi_multitype_results,
    plot_epi_skyline_results,
    plot_fbd_2traits_results,
    plot_fbd_no_traits_results,
    plot_scenarios,
)


def generate_figures():
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["xtick.labelsize"] = 14
    plt.rcParams["ytick.labelsize"] = 14
    plt.rcParams["font.size"] = 14
    plt.rcParams["figure.constrained_layout.use"] = True
    plt.rcParams["lines.linewidth"] = 3

    plot_scenarios()
    plot_epi_skyline_results()
    plot_epi_multitype_results()
    plot_fbd_no_traits_results()
    plot_fbd_2traits_results()
