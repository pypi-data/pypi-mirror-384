import re
from operator import itemgetter

import pandas as pd
import pytest

import genno
from genno import Computer
from genno.core.describe import label
from genno.core.sparsedataarray import SparseDataArray


@pytest.mark.usefixtures("parametrize_quantity_class")
def test_describe():
    c = Computer()
    c.add("foo", genno.Quantity(pd.Series([42, 43])))

    if genno.Quantity is SparseDataArray:
        assert re.match(
            r"""'foo':
- <xarray\.SparseDataArray \([^:]+: 2\)>""",
            c.describe("foo"),
        )


def test_describe_shorten():
    c = Computer()
    c.add_single("foo", len, dict([(f"key{N}", "X" * N) for N in range(10)]))

    assert (
        """'config':
- {}

'foo':
- <built-in len>
- {'key0': '', 'key1': 'X', 'key2': 'XX', 'key3': 'XXX', 'key4': 'XXXX', 'key5': 'XXXXX', 'key6': 'XXXXXX', 'key7': 'XXXXXXX', 'key8': 'XXXXXXXX', 'key9': [...]

all"""  # noqa: E501
        == c.describe()
    )


def test_describe_cyclic():
    """Test that :meth:`.describe` works on a cyclic graph without RecursionError."""

    c = Computer()

    c["x"] = "mul", 1, 2
    c["y"] = "concat", "x", "z:"
    c["z"] = "add", "y", 0.5

    assert "CYCLE DETECTED" in c.describe("z")


def test_label():
    """:func:`label` handles unusual callables."""
    assert "operator.itemgetter(0)" == label(itemgetter(0))
