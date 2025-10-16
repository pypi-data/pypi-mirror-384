"""Test legend."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from .helpers import assert_equality

mpl.use("Agg")


def plot() -> Figure:
    fig, ax = plt.subplots(3, 3, sharex="col", sharey="row")
    axes = [ax[i][j] for i in range(len(ax)) for j in range(len(ax[i]))]
    for k, loc in enumerate(range(2, 11)):
        t1 = np.arange(0.0, 2.0, 0.4)
        t2 = np.arange(0.0, 2.0, 0.4)

        # note that plot returns a list of lines. The 'l1, = plot' usage extracts the
        # first element of the list into l1 using tuple unpacking. So l1 is a Line2D
        # instance, not a sequence of lines
        (l1,) = axes[k].plot(t2, np.exp(-t2), linewidth=0.5)
        axes[k].plot(t2, np.sin(2 * np.pi * t2), "--go", t1, np.log(1 + t1), ".")
        axes[k].plot(t2, np.exp(-t2) * np.sin(2 * np.pi * t2), "rs-.")

        axes[k].legend((l1,), (f"loc {loc:d}",), loc=loc)
    return fig


def test() -> None:
    assert_equality(plot, __file__[:-3] + "_reference.tex")
