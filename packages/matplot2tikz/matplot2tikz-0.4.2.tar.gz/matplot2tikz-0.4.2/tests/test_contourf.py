"""Test contourf plot."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from .helpers import assert_equality

mpl.use("Agg")


def plot() -> Figure:
    nbins = 5

    fig = plt.figure()
    ax = plt.gca()

    x_max = 2
    x_min = 0
    y_max = 2
    y_min = 0

    yi, xi = np.meshgrid(np.linspace(y_min, y_max, nbins), np.linspace(x_min, x_max, nbins))
    pos = np.empty((*xi.shape, 2))
    pos[:, :, 0] = xi
    pos[:, :, 1] = yi
    zi = 2 - (xi - 1) ** 2 - (yi - 1) ** 2
    ax.contourf(xi, yi, zi, levels=5)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    return fig


def test() -> None:
    try:
        assert_equality(plot, __file__[:-3] + "_reference.tex")
    except AssertionError:
        # Try other output, which is the new output since Python 3.9
        assert_equality(plot, __file__[:-3] + "_reference2.tex")
