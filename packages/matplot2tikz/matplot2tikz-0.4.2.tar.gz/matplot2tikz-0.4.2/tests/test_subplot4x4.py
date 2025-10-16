"""Test a 4x4 subplot."""

import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from .helpers import assert_equality

mpl.use("Agg")


def plot() -> Figure:
    fig = plt.figure()

    an = np.linspace(0, 2 * np.pi, 10)

    plt.subplot(221)
    plt.plot(3 * np.cos(an), 3 * np.sin(an))
    plt.title("not equal, looks like ellipse", fontsize=10)

    plt.subplot(222)
    plt.plot(3 * np.cos(an), 3 * np.sin(an))
    plt.axis("equal")
    plt.title("equal, looks like circle", fontsize=10)

    plt.subplot(223)
    plt.plot(3 * np.cos(an), 3 * np.sin(an))
    plt.axis("equal")
    plt.axis((-3, 3, -3, 3))
    plt.title("looks like circle, even after changing limits", fontsize=10)

    plt.subplot(224)
    plt.plot(3 * np.cos(an), 3 * np.sin(an))
    plt.axis("equal")
    plt.axis((-3, 3, -3, 3))
    plt.plot([0, 4], [0, 4])
    plt.title("still equal after adding line", fontsize=10)

    return fig


def test() -> None:
    assert_equality(plot, __file__[:-3] + "_reference.tex")
