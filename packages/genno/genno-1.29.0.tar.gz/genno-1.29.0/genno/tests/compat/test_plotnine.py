import logging
import re
from pathlib import Path

import plotnine as p9
import pytest

from genno import Computer, MissingKeyError, Quantity
from genno.compat.plotnine import Plot


class Plot1(Plot):
    inputs = ["x:t", "y:t"]


class Plot2(Plot):
    basename = "test"
    suffix = ".svg"

    def generate(self, x, y):
        return p9.ggplot(x.merge(y, on="t"), p9.aes(x="x", y="y")) + p9.geom_point()


class Plot3(Plot2):
    """Concrete Plot subclasses can be further subclassed."""

    suffix = ".pdf"
    inputs = ["x:t", "y:t"]

    def generate(self, x, y):
        """Return an iterable of 2 plots."""
        return (super().generate(x, y), super().generate(x, y))


class Plot4(Plot3):
    """Plot that requires a non-existent key as an input."""

    inputs = ["x:t", "notakey"]


@pytest.mark.usefixtures("parametrize_copy_on_write")
def test_Plot(caplog, tmp_path):
    c = Computer(output_dir=tmp_path)
    t = {"t": [-1, 0, 1]}
    c.add("x:t", Quantity([1.0, 2, 3], coords=t, name="x"))
    c.add("y:t", Quantity([1.0, 2, 3], coords=t, name="y"))

    # Exception raised when the class is incomplete

    with pytest.raises(
        TypeError,
        # Messages vary by Python version:
        # - 3.9–3.11: "…with abstract method generate" (no s)
        # - 3.12    : "…without an implementation for abstract method 'generate'"
        match=(
            "Can't instantiate abstract class Plot1 with.* abstract method.*generate"
        ),
    ):
        c.add("plot", Plot1)

    c.add("plot", Plot2, "x:t", "y:t")

    # Graph contains the task. Don't compare the callable
    assert ("config", "x:t", "y:t") == c.graph["plot"][1:]
    assert callable(c.graph["plot"][0])

    # Plot can be generated
    result = c.get("plot")

    # Result is the path to the file
    assert isinstance(result, Path)

    # Concrete Plot subclasses can be further subclassed

    # Multi-page PDFs can be saved
    c.add("plot", Plot3)
    c.get("plot")

    # Raised during add(…, strict=True)
    with pytest.raises(MissingKeyError, match=re.escape("required keys ('notakey',)")):
        c.add("plot4", Plot4, strict=True)

    # Logged during get()
    c.add("plot", Plot4)
    c.get("plot")

    assert "Missing input(s) ('notakey',) to plot 'test'; no output" in caplog.messages


def test_Plot_deprecated(caplog, tmp_path):
    """Same as above, but using deprecated Plot.make_task()."""
    c = Computer(output_dir=tmp_path)
    t = {"t": [-1, 0, 1]}
    c.add("x:t", Quantity([1.0, 2, 3], coords=t, name="x"))
    c.add("y:t", Quantity([1.0, 2, 3], coords=t, name="y"))

    with pytest.warns(DeprecationWarning):
        c.add("plot", Plot2.make_task("x:t", "y:t"))

    # Graph contains the task. Don't compare the callable
    assert ("config", "x:t", "y:t") == c.graph["plot"][1:]
    assert callable(c.graph["plot"][0])

    # Plot can be generated
    result = c.get("plot")

    # Result is the path to the file
    assert isinstance(result, Path)

    # Concrete Plot subclasses can be further subclassed

    # Multi-page PDFs can be saved
    with pytest.warns(DeprecationWarning):
        c.add("plot", Plot3.make_task())
    c.get("plot")

    # Raised during add(…, strict=True)
    with (
        pytest.raises(MissingKeyError, match=re.escape("required keys ('notakey',)")),
        pytest.warns(DeprecationWarning),
    ):
        c.add("plot4", Plot4.make_task(), strict=True)

    # Logged during get()
    with pytest.warns(DeprecationWarning):
        c.add("plot", Plot4.make_task())
    c.get("plot")

    assert "Missing input(s) ('notakey',) to plot 'test'; no output" in caplog.messages


def test_plot_none(caplog, tmp_path):
    """Messages are logged when Plot.generate() returns nothing."""
    caplog.set_level(logging.INFO)
    c = Computer(output_dir=tmp_path)

    class Plot1(Plot):
        basename = "test-1"

        def generate(self):
            return None

    class Plot2(Plot):
        basename = "test-2"

        def generate(self):
            return []

    c.add("plot-1", Plot1)
    # Returns None
    assert c.get("plot-1") is None
    # Message is logged
    assert "Plot1.generate() returned None; no output" == caplog.messages[-1]

    caplog.clear()

    c.add("plot-2", Plot2)
    assert c.get("plot-2") is None
    assert "Plot2.generate() returned []; no output" == caplog.messages[-1]
