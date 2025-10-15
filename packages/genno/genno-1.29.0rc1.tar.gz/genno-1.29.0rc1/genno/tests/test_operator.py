import logging
import random
import re
from collections.abc import Hashable, Iterable, Mapping
from contextlib import nullcontext
from functools import partial
from itertools import compress

import numpy as np
import pandas as pd
import pint
import pytest
import xarray as xr
from numpy.testing import assert_allclose
from pandas.testing import assert_series_equal

import genno
from genno import Computer, operator, quote
from genno.core.sparsedataarray import SparseDataArray
from genno.operator import random_qty
from genno.testing import (
    MARK,
    add_large_data,
    add_test_data,
    assert_logs,
    assert_qty_allclose,
    assert_qty_equal,
    assert_units,
)

pytestmark = pytest.mark.usefixtures("parametrize_quantity_class")


@pytest.fixture(scope="function")
def data():
    """Yields a computer, then the values of :func:`.add_test_data`."""
    c = Computer()
    yield [c] + list(add_test_data(c))


def test_as_quantity() -> None:
    # str
    r1 = operator.as_quantity("3.0 kg")
    assert_units(r1, "kg")

    # dict
    value = {
        ("x0", "y0"): 1.0,
        ("x1", "y1"): 2.0,
        "_dim": ("x", "y"),
        "_unit": "km",
    }
    r2 = operator.as_quantity(value)
    assert {"x", "y"} == set(r2.dims)
    assert_units(r2, "km")

    r3 = operator.as_quantity(1.2)
    assert not r3.dims
    assert_units(r3, "dimensionless")

    with pytest.raises(TypeError):
        operator.as_quantity(set())  # type: ignore


def test_clip(data) -> None:
    *_, x = data

    # Only min=
    r1 = operator.clip(x, 0.49)
    assert 0.49 == r1.min()
    assert x.name == r1.name
    assert x.units == r1.units

    # Only max=
    r2 = operator.clip(x, None, 0.51)
    assert 0.51 == r2.max()

    # Both min= and max=
    r3 = operator.clip(x, 0.49, 0.51)
    assert 0.49 == r3.min()
    assert 0.51 == r2.max()


@pytest.mark.xfail(
    reason="Runs twice for parametrize_quantity_class, but only warns once"
)
def test_deprecated_import():
    with pytest.warns(FutureWarning, match="use genno.operator instead"):
        from genno.computations import add  # noqa: F401


@pytest.mark.parametrize(
    "op, expected_dims",
    (
        (operator.add, ("a", "b", "c")),
        (operator.sub, ("a", "b", "c")),
        (operator.mul, ("a", "b", "c")),
        (operator.div, ("a", "b", "c")),
    ),
)
def test_dims(op, expected_dims):
    c = Computer()
    x = c.add("x:a-b", None)
    y = c.add("y:b-c", None)

    key = c.add("z", op, x, y)
    # print(f"{key = }")
    assert expected_dims == key.dims


@pytest.mark.parametrize(
    "expr, expected_dims",
    (
        ("z = x + y", ("a", "b", "c")),  # operator.add
        ("z = x - y", ("a", "b", "c")),  # operator.sub
        ("z = x * y", ("a", "b", "c")),  # operator.mul
        ("z = x / y", ("a", "b", "c")),  # operator.div
    ),
)
def test_dims_eval(expr, expected_dims):
    c = Computer()
    c.add("x:a-b", None)
    c.add("y:b-c", None)

    key, *_ = c.eval(expr)
    assert expected_dims == key.dims


@pytest.mark.parametrize(
    "operands, shape",
    [
        (("a", "a"), (3, 6)),
        (("a", "x"), (6, 6)),
        (("x", "b"), (6, 6)),
        (("a", "b"), (6, 6)),
        (("a", "x", "b"), (6, 6)),
    ],
)
def test_add(data, operands, shape, recwarn):
    # Unpack
    c, t, t_foo, t_bar, x = data

    y = c.get("y")
    x = c.get("x:t-y")
    a = genno.Quantity(
        np.random.rand(len(t_foo), len(y)), coords={"t": t_foo, "y": y}, units=x.units
    )
    b = genno.Quantity(
        np.random.rand(len(t_bar), len(y)), coords={"t": t_bar, "y": y}, units=x.units
    )

    c.add("a:t-y", a)
    c.add("b:t-y", b)

    key = c.add("result", tuple([operator.add] + [f"{name}:t-y" for name in operands]))

    result = c.get(key)
    assert shape == result.shape, result.to_series()


def test_add_units():
    """Units are handled correctly by :func:`.add`."""
    A = genno.Quantity(1.0, units="kg")
    B = genno.Quantity(1.0, units="tonne")

    # Units of result are units of the first argument
    assert_qty_equal(genno.Quantity(1001.0, units="kg"), operator.add(A, B))
    assert_qty_equal(genno.Quantity(1.001, units="tonne"), operator.add(B, A))

    with pytest.raises(
        pint.DimensionalityError, match="Cannot convert .*length.* to .*mass"
    ):
        operator.add(A, genno.Quantity(1.0, units="km"))


@pytest.mark.parametrize("keep", (True, False))
def test_aggregate0(caplog, data, keep):
    *_, t_foo, t_bar, x = data

    t_groups = dict(foo=t_foo, bar=t_bar)

    result = operator.aggregate(x, dict(t=t_groups), keep)
    assert result.name == x.name and result.units == x.units  # Pass through

    # Result has the expected dimensions
    assert set(t_groups) | (set(t_foo + t_bar) if keep else set()) == set(
        result.coords["t"].data
    )

    # Now with a group ID that duplicates one of the existing index names
    t_groups[t_foo[0]] = t_foo[:1]
    with (
        assert_logs(
            caplog, f"t='{t_foo[0]}' is already present in quantity 'Quantity X'"
        )
        if keep
        else nullcontext()
    ):
        result = operator.aggregate(x, dict(t=t_groups), keep)

    # Two dimensions
    result = operator.aggregate(x, {"t": t_groups, "y": {"2k": [2000, 2010]}}, keep)
    assert "2k" in result.coords["y"]


@pytest.mark.parametrize("keep", (True, False))
def test_aggregate_regex(caplog, data, keep):
    """:func:`aggregate` using regular expressions."""
    *_, t_foo, t_bar, x = data

    # Aggregate using regular expressions
    t_groups = dict(foo=[re.compile("foo[123]")], bar=[re.compile("b[ar]{2}.")])

    # Operation completes
    result = operator.aggregate(x, dict(t=t_groups), keep)

    # Name and units pass through
    assert result.name == x.name and result.units == x.units

    # Result has the expected dimensions
    assert set(t_groups) | (set(t_foo + t_bar) if keep else set()) == set(
        result.coords["t"].data
    )


def test_apply_units(data, caplog):
    # Unpack
    *_, x = data

    registry = pint.get_application_registry()

    # Brute-force replacement with incompatible units
    with assert_logs(
        caplog, "Replace 'kilogram' with incompatible 'liter'", at_level=logging.DEBUG
    ):
        result = operator.apply_units(x, "litres")
    assert result.units == registry.Unit("litre")
    # No change in values
    assert_series_equal(result.to_series(), x.to_series())
    assert result.name == x.name  # Pass through

    # Compatible units: magnitudes are also converted
    with assert_logs(
        caplog, "Convert 'kilogram' to 'metric_ton'", at_level=logging.DEBUG
    ):
        result = operator.apply_units(x, "tonne")
    assert result.units == registry.Unit("tonne")
    assert_series_equal(result.to_series(), 0.001 * x.to_series(), check_like=True)

    # Remove unit
    x.units = registry.Unit("dimensionless")

    caplog.clear()
    result = operator.apply_units(x, "kg")
    # Nothing logged when _unit attr is missing
    assert len(caplog.messages) == 0
    assert result.units == registry.Unit("kg")
    assert_series_equal(result.to_series(), x.to_series())


def test_assign_units(data, caplog):
    # Unpack
    *_, x = data

    registry = pint.get_application_registry()

    # Brute-force replacement with incompatible units
    with assert_logs(
        caplog,
        "Replace 'kilogram' with 'liter' with different dimensionality",
        at_level=logging.INFO,
    ):
        result = operator.assign_units(x, "litres")
    assert result.units == registry.Unit("litre")
    # No change in values
    assert_series_equal(result.to_series(), x.to_series())
    assert result.name == x.name  # Pass through

    # Compatible units: magnitudes are not changed
    with assert_logs(
        caplog,
        "Replace 'kilogram' with 'metric_ton' without altering magnitudes",
        at_level=logging.INFO,
    ):
        result = operator.assign_units(x, "tonne")
    assert result.units == registry.Unit("tonne")
    assert_series_equal(result.to_series(), x.to_series())

    # Remove unit
    x.units = registry.Unit("dimensionless")

    caplog.clear()
    result = operator.assign_units(x, "kg")
    # Nothing logged when _unit attr is missing
    assert len(caplog.messages) == 0
    assert result.units == registry.Unit("kg")
    assert_series_equal(result.to_series(), x.to_series())


def test_convert_units(data, caplog):
    # Unpack
    *_, x = data

    registry = pint.get_application_registry()

    # Brute-force replacement with incompatible units
    with pytest.raises(ValueError, match="cannot be converted to"):
        result = operator.convert_units(x, "litres")

    # Compatible units: magnitudes are also converted
    result = operator.convert_units(x, "tonne")
    assert registry.Unit("tonne") == result.units
    assert_series_equal(
        result.to_series(), (x.to_series() * 0.001).rename("Quantity X")
    )
    assert result.name == x.name  # Pass through

    # Remove unit
    x.units = registry.Unit("dimensionless")

    with pytest.raises(ValueError, match="cannot be converted to"):
        result = operator.convert_units(x, "kg")


@pytest.mark.parametrize(
    "map_values, kwarg",
    (
        ([[1.0, 1, 0], [0, 0, 1]], dict()),
        pytest.param(
            [[1.0, 1, 0], [0, 1, 1]],
            dict(strict=True),
            marks=pytest.mark.xfail(raises=ValueError, reason="invalid map"),
        ),
    ),
)
def test_broadcast_map(map_values, kwarg):
    x = ["x1"]
    y = ["y1", "y2"]
    z = ["z1", "z2", "z3"]
    q = genno.Quantity([[42.0, 43]], coords={"x": x, "y": y})
    m = genno.Quantity(map_values, coords={"y": y, "z": z})

    result = operator.broadcast_map(q, m, **kwarg)
    exp = genno.Quantity([[42.0, 42, 43]], coords={"x": x, "z": z}, units="")

    assert_qty_equal(exp, result)


def test_combine(ureg, data):
    *_, t_bar, x = data

    # Without select, preserves the "t" dimension
    result = operator.combine(x, x, x, weights=(-1, 0.2, 0.8))

    assert ("t", "y") == result.dims
    assert 36 == result.size
    assert all(1e-15 > result.to_series().values)

    # With select, the selected values are summed along the "t" dimension
    result = operator.combine(
        x, x, select=(dict(t=t_bar), dict(t=t_bar)), weights=(-1, 1)
    )

    assert ("y",) == result.dims
    assert 6 == result.size
    assert all(1e-15 > result.to_series().values)

    # Incompatible units raises ValueError
    x2 = genno.Quantity(x, units=ureg.metre)
    with pytest.raises(
        ValueError, match=re.escape("Cannot combine() units kilogram and meter")
    ):
        operator.combine(x, x2, select=(dict(t=t_bar), dict(t=t_bar)), weights=(-1, 1))


def test_concat(ureg, data):
    *_, t_foo, t_bar, x = data

    # Split x into two concatenateable quantities
    a = operator.select(x, dict(t=t_foo))
    b = operator.select(x, dict(t=t_bar))

    # Concatenate
    operator.concat(a, b, dim="t")

    # Concatenate twice on a new dimension
    result = operator.concat(x, x, dim=pd.Index(["z1", "z2"], name="z"))

    # NB for AttrSeries, the new dimension is first; for SparseDataArray, last
    assert {"t", "y", "z"} == set(result.dims)
    assert ureg.Unit("kg") == x.units == result.units


def test_concat_dim_order(data):
    """:func:`.concat` succeeds even if dimension are not in matching order on operands.

    Test of https://github.com/khaeru/genno/issues/38.
    """
    *_, x = data

    # Create another Quantity like `x`, but with dims in the opposite order
    z = genno.Quantity(
        x.to_series()
        .reset_index()
        .eval("y = y + 1000")
        .set_index(list(reversed(x.dims)))
        .iloc[:, 0]
    )
    assert tuple(reversed(x.dims)) == z.dims

    # Concatenation succeeds
    result = operator.concat(x, z)

    # Dims and length are as expected
    assert set(x.dims) == set(z.dims) == set(result.dims)
    assert len(x) + len(z) == len(result)

    # Dimensions were aligned correctly such that "y" in the result contains labels from
    # the same dimension in both operands
    assert set(x.coords["y"].data) | set(z.coords["y"].data) == set(
        result.coords["y"].data
    )


@pytest.mark.parametrize("func", [operator.div, operator.ratio])
def test_div(func, ureg):
    # Non-overlapping dimensions can be broadcast together
    A = random_qty(dict(x=3, y=4), units="km")
    B = random_qty(dict(z=2), units="hour")

    result = func(A, B)
    assert ("x", "y", "z") == result.dims
    assert ureg.Unit("km / hour") == result.units


def test_div_scalar(data, ureg):
    """:func:`.div` handles scalar numerator."""

    *_, x = data

    result = operator.div(2.0, x)
    assert ("t", "y") == result.dims
    assert_qty_equal(
        2.0 / x.sel(t="foo1", y=2000), result.sel(t="foo1", y=2000), check_attrs=False
    )


def test_drop_vars(data):
    # Unpack
    *_, x = data

    result = operator.drop_vars(x, "t")
    assert result.name == x.name and result.units == x.units  # Pass through
    assert set(x.dims) == {"t"} | set(result.dims)


@pytest.mark.parametrize(
    "shape_in",
    (
        dict(),  # 0 dimensions
        dict(x=2),  # 1 dimension
        dict(x=2, y=2, z=2),  # >1 dimension
    ),
)
def test_expand_dims0(shape_in):
    q_in = random_qty(shape_in, units="kg")

    def _shape(q):
        return dict(zip(q.dims, q.shape))

    # …no arguments → no-op
    result0 = operator.expand_dims(q_in, {})
    assert shape_in == _shape(result0)

    # …single hashable → 1 dim of length 1
    result1 = operator.expand_dims(q_in, "a")
    assert dict(a=1) | shape_in == _shape(result1)

    # …iterable of dimension IDs
    result2 = operator.expand_dims(q_in, tuple("ab"))
    assert dict(a=1, b=1) | shape_in == _shape(result2)
    assert_units(result2, "kg")

    # …dict of dimension lengths
    result3 = operator.expand_dims(q_in, dict(a=2, b=3))
    assert dict(a=2, b=3) | shape_in == _shape(result3)
    assert [0, 1] == result3.coords["a"].data.tolist()

    # …kwargs with dimension lengths
    result4 = operator.expand_dims(q_in, a=2, b=3)
    assert dict(a=2, b=3) | shape_in == _shape(result4)
    assert [0, 1] == result4.coords["a"].data.tolist()

    # …dict of dimension values
    result5 = operator.expand_dims(q_in, dict(a=["a0", "a1"], b=["b0", "b1", "b2"]))
    assert dict(a=2, b=3) | shape_in == _shape(result5)
    assert ["a0", "a1"] == result5.coords["a"].data.tolist()

    # …kwargs with dimension values
    result6 = operator.expand_dims(q_in, a=["a0", "a1"], b=["b0", "b1", "b2"])
    assert dict(a=2, b=3) | shape_in == _shape(result6)
    assert ["a0", "a1"] == result6.coords["a"].data.tolist()

    # …dict of dimension with empty list values
    result7 = operator.expand_dims(q_in, dict(a=[], b=[]))
    with (
        pytest.raises(AssertionError)
        if isinstance(q_in, SparseDataArray)
        else nullcontext()
    ):
        assert dict(a=1, b=1) | shape_in == _shape(result7)

    # …kwarg with empty list values
    result8 = operator.expand_dims(q_in, a=[], b=[])
    with (
        pytest.raises(AssertionError)
        if isinstance(q_in, SparseDataArray)
        else nullcontext()
    ):
        assert dict(a=1, b=1) | shape_in == _shape(result8)


def test_expand_dims1() -> None:
    q_in = random_qty(dict(), units="kg")

    with pytest.raises(TypeError):
        operator.expand_dims(q_in, 1)

    with pytest.raises(ValueError):
        operator.expand_dims(q_in, ["a", "b", "a"])


def test_group_sum(ureg):
    X = random_qty(dict(a=2, b=3), units=ureg.kg, name="Foo")

    result = operator.group_sum(X, "a", "b")
    assert result.name == X.name and result.units == X.units  # Pass through
    assert ("a",) == result.dims
    assert 2 == len(result)


def test_index_to(ureg):
    q = random_qty(dict(x=3, y=5))
    q.name = "Foo"
    q.units = ureg.kg

    # Ensure that the dimension "x" is dropped from the denominator
    denom = q.sel(x="x0")
    assert "x" not in denom.dims

    exp = q / denom
    exp.units = ""  # Indexed values are dimensionless
    assert exp.dims == q.dims

    # Called with a mapping
    result = operator.index_to(q, dict(x="x0"))
    assert_qty_equal(exp, result)
    assert exp.name == result.name

    # Called with two positional arguments
    result = operator.index_to(q, "x", "x0")
    assert_qty_equal(exp, result)

    # Default first index selected if 'None' is given
    result = operator.index_to(q, "x")
    assert_qty_equal(exp, result)

    result = operator.index_to(q, dict(x=None))
    assert_qty_equal(exp, result)

    # Invalid calls
    with pytest.raises(TypeError, match="expected a mapping from 1 key to 1 value"):
        operator.index_to(q, dict(x="x0", y="y0"))  # Length != 1

    with pytest.raises(KeyError):
        operator.index_to(q, dict(x="x99"))  # Mapping to something invalid


@pytest.mark.parametrize(
    "shape",
    [
        dict(x=3),
        dict(x=3, y=3),
        dict(y=3, x=3),
        dict(x=3, y=3, z=2),
        dict(y=3, x=3, z=2),
        dict(y=3, z=2, x=3),
    ],
)
def test_interpolate(caplog, ureg, shape):
    """Test :func:`.interpolate`."""
    # Generate a random quantity with one dimension indexed by integers
    q = random_qty(shape, name="Foo", units=ureg.kg)
    x = [2020, 2030, 2040]
    q = q.assign_coords({"x": x})

    # Linear interpolation of 1 point
    result = operator.interpolate(q, dict(x=2025), assume_sorted=False)
    assert result.name == q.name and result.units == q.units  # Pass through
    assert "interpolate(…, assume_sorted=False) ignored" in caplog.messages

    # Result has the expected class, dimensions, and values
    assert isinstance(result, q.__class__)
    assert tuple([d for d in q.dims if d != "x"]) == result.dims
    assert_qty_allclose(
        result, 0.5 * q.sel(x=[2020, 2030]).sum("x"), ignore_extra_coords=True
    )

    # Extrapolation on both ends of the data
    x = sorted(x + [x[0] - 1, x[-1] + 1])

    # interpolate() works
    result = operator.interpolate(
        q, dict(x=x), method="linear", kwargs=dict(fill_value="extrapolate")
    )

    # Produces the expected results
    r = result
    for i1, i2, i3 in ((0, 1, 2), (-1, -2, -3)):
        # Slope interior to the existing data
        slope_int = (r.sel(x=x[i3], drop=True) - r.sel(x=x[i2], drop=True)) / (
            x[i3] - x[i2]
        )
        # Slope to extrapolated points
        slope_ext = (r.sel(x=x[i2], drop=True) - r.sel(x=x[i1], drop=True)) / (
            x[i2] - x[i1]
        )
        # print(
        #     (i1, x[i1], r.sel(x=x[i1])),
        #     (i2, x[i2], r.sel(x=x[i2])),
        #     (i3, x[i3], r.sel(x=x[i3])),
        #     slope_int,
        #     slope_ext,
        # )
        assert_qty_allclose(slope_int, slope_ext)


@pytest.mark.parametrize(
    "name, kwargs",
    [
        ("input0.csv", dict(units="km")),
        # Units kwarg as a pint.Quantity
        ("input0.csv", dict(units=pint.get_application_registry()("1.0 km"))),
        # Dimensions as a container, without mapping
        ("input0.csv", dict(dims=["i", "j"], units="km")),
        #
        # Map a dimension name from the file to a different one in the quantity; ignore
        # dimension "foo"
        ("input1.csv", dict(dims=dict(i="i", j_dim="j"))),
        ("input2.csv", dict(dims=["i", "j"])),
        ("input2.csv", dict(dims=["i", "j"], units="km")),  # Logs a warning
        # Exceptions
        pytest.param(
            "input1.csv",
            dict(dims=dict(i="i", j_dim="j"), units="kg"),
            marks=pytest.mark.xfail(
                raises=ValueError, reason="Explicit units 'kg' do not match 'km'…"
            ),
        ),
        pytest.param(
            "load_file-invalid.csv",
            dict(),
            marks=pytest.mark.xfail(
                raises=ValueError, reason="with non-unique units array(['cm'], ['km'],"
            ),
        ),
    ],
)
def test_load_file(test_data_path, ureg, name, kwargs):
    qty = operator.load_file(test_data_path / name, name="baz", **kwargs)

    assert ("i", "j") == qty.dims
    assert ureg.kilometre == qty.units
    assert "baz" == qty.name


@pytest.mark.parametrize(
    "func",
    (
        operator.mul,
        operator.product,  # Alias
        operator.disaggregate_shares,  # Deprecated alias
    ),
)
def test_mul0(func):
    A = genno.Quantity([1.0, 2], coords={"a": ["a0", "a1"]})
    B = genno.Quantity([3.0, 4], coords={"b": ["b0", "b1"]})
    exp = genno.Quantity(
        [[3.0, 4], [6, 8]], coords={"a": ["a0", "a1"], "b": ["b0", "b1"]}, units="1"
    )

    assert_qty_equal(exp, func(A, B))


@pytest.mark.parametrize("func", [operator.mul, operator.product])
@pytest.mark.parametrize(
    "dims, exp_dims, exp_shape",
    (
        # Scalar × scalar
        (({}, {}), tuple(), tuple()),
        # Scalar × 1D
        (({}, dict(a=2)), ("a",), (2,)),
        # 1D × scalar
        ((dict(a=2), {}), ("a",), (2,)),
        # 1D with disjoint dimensions ** 3 = 3D
        ((dict(a=2), dict(b=2), dict(c=2)), tuple("abc"), (2, 2, 2)),
        # 2D × scalar × scalar = 2D
        ((dict(a=2, b=2), {}, {}), tuple("ab"), (2, 2)),
        # scalar × 1D × scalar = 1D
        (({}, dict(a=2), {}), tuple("a"), (2,)),
        # 4D × 5D, with some overlapping dimensions
        (
            (dict(a=2, b=2, c=2, d=2), dict(b=2, c=2, d=2, e=2, f=2)),
            tuple("abcdef"),
            (2, 2, 2, 2, 2, 2),
        ),
    ),
)
def test_mul1(func, dims, exp_dims, exp_shape):
    """Product of quantities with disjoint and overlapping dimensions."""
    quantities = [random_qty(d) for d in dims]

    result = func(*quantities)

    assert exp_dims == result.dims
    assert exp_shape == result.shape


@pytest.mark.parametrize(
    "exponent, base_units, exp_units",
    (
        # 2D dimensionless ** float
        (1.2, None, None),
        # 2D with units ** int
        (2, "kg", "kg ** 2"),
        # 2D ** 1D int
        (pd.Series(dict(y1=1, y2=2, y3=3)), "kg", ""),
        # 2D ** 1D int, all values the same
        (pd.Series(dict(y1=2, y2=2, y3=2)), "kg", "kg ** 2"),
        # 2D ** 1D with units
        pytest.param(
            random_qty(dict(y=3), units="km"),
            None,
            None,
            marks=pytest.mark.xfail(
                raises=ValueError, reason="Cannot raise to a power with units (km)"
            ),
        ),
    ),
)
def test_pow_simple(ureg, exponent, base_units, exp_units):
    A = random_qty(dict(x=3, y=3), units=base_units)

    # Convert using the current Quantity class
    if isinstance(exponent, pd.Series):
        exponent = genno.Quantity(exponent)

    result = operator.pow(A, exponent)
    assert exp_units is None or ureg.Unit(exp_units) == result.units


def test_pow(ureg):
    A = random_qty(dict(x=3, y=3))

    # 2D dimensionless ** int
    result = operator.pow(A, 2)
    # Expected values
    assert_qty_equal(A.sel(x="x1", y="y1") ** 2, result.sel(x="x1", y="y1"))

    # 2D ** 1D float
    B = random_qty(dict(y=3))
    result = operator.pow(A, B)
    # Expected values
    assert_allclose(
        A.sel(x="x1", y="y1").item() ** B.sel(y="y1").item(),
        result.sel(x="x1", y="y1").item(),
    )
    assert ureg.dimensionless == result.units


def test_relabel(data):
    # Unpack
    c, t, t_foo, t_bar, x = data

    # Mapping from old to new labels for each dimension
    args = dict(
        t={"foo2": "baz", "bar5": "qux", "nothing": "nothing"},
        y={2030: 3030},
        not_a_dimension=None,
    )

    def check(qty):
        # Dimension t was relabeled
        t_out = set(qty.coords["t"].data)
        assert {"baz", "qux"} < t_out and not {"foo2", "bar5"} & t_out
        # Dimension y was relabeled
        assert 3030 in result.coords["y"] and 2030 not in result.coords["y"]

    # Can be called with a dictionary
    result = operator.relabel(x, args)
    check(result)
    assert result.name == x.name and result.units == x.units  # Pass through

    # Can be added and used through Computer

    # Store the name map in the Computer
    c.add("labels", quote(args))

    # Test multiple ways of adding this computation
    for args in [
        ("test", operator.relabel, "x:t-y", args),
        ("test", partial(operator.relabel, **args), "x:t-y"),
        ("test", "relabel", "x:t-y", args),
        ("test", "relabel", "x:t-y", "labels"),
        # Deprecated
        ("relabel", "test", "x:t-y", args),
        ("relabel", "test", "x:t-y", "labels"),
    ]:
        c.add(*args)
        result = c.get("test")
        check(result)


@pytest.mark.parametrize("func", [operator.rename, operator.rename_dims])
def test_rename(data, func):
    """Test both :func:`.rename` and :func:`.rename_dims`."""
    # Unpack
    c, t, t_foo, t_bar, x = data

    # Can be called with a string
    assert "New name" == func(x, "New name").name

    # Can be called with a dictionary
    args = {"t": "s", "y": "z"}
    result = func(x, args)
    assert result.name == x.name and result.units == x.units  # Pass through
    assert ("s", "z") == result.dims  # Quantity has renamed dimensions
    # Renamed dimension contains original labels
    assert set(t) == set(result.coords["s"].data)

    # Can be called with keyword arguments
    result = func(x, **args)
    # As above
    assert ("s", "z") == result.dims and set(t) == set(result.coords["s"].data)

    with pytest.raises(ValueError, match="cannot specify both keyword and positional"):
        func(x, args, **args)

    # Can be added and used through Computer

    # Store the name map in the Computer
    c.add("dim name map", quote(args))

    # Test multiple ways of adding this computation
    for args in [
        ("test", func, "x:t-y", args),
        ("test", partial(func, **args), "x:t-y"),
        ("test", "rename_dims", "x:t-y", args),
        ("test", "rename_dims", "x:t-y", "dim name map"),
        ("test", "rename", "x:t-y", args),
        ("test", "rename", "x:t-y", "dim name map"),
        # Deprecated
        ("rename_dims", "test", "x:t-y", args),
        ("rename_dims", "test", "x:t-y", "dim name map"),
    ]:
        c.add(*args)
        result = c.get("test")
        # As above
        assert ("s", "z") == result.dims and set(t) == set(result.coords["s"].data)


def test_round(data):
    # Unpack
    *_, x = data

    # Up to 36 unique random values in `x`
    assert 2 < len(x.to_series().unique()) <= 36

    # round() runs
    result0 = operator.round(x)
    assert result0.name == x.name and result0.units == x.units

    # Only 0 or 1
    assert {0.0, 1.0} >= set(result0.to_series().unique())

    # round to 1 decimal place
    result1 = operator.round(x, 1)
    assert 0 <= len(result1.to_series().unique()) <= 11


@pytest.mark.parametrize(
    "indexers, kwargs, exp_dims, exp_shape",
    (
        # Length-1 indexer but drop=False (default) results in 2D data
        ({"y": [2010]}, {}, ("t", "y"), (6, 1)),
        # Same, with an additional non-existent label → same result
        ({"y": [2010, 9999]}, {}, ("t", "y"), (6, 1)),
        # Scalar indexer with drop=True results in 1D data
        ({"y": 2010}, dict(drop=True), ("t",), (6,)),
        # Length-1 indexer with drop=True results in 2D data
        ({"y": [2010]}, dict(drop=True), ("t", "y"), (6, 1)),
        # Scalar indexer with nonexistent label -> KeyError
        pytest.param({"y": 9999}, {}, (), (), marks=pytest.mark.xfail(raises=KeyError)),
        # Length-1 indexer with nonexistent label
        # NB this gives shape (6, 0) with SparseDataArray; (0, 0) with AttrSeries; test
        #    the size instead
        ({"y": [9999]}, {}, ("t", "y"), 0),
        # With inverse=True, the given label is dropped from the given dimension
        ({"y": [2010]}, dict(inverse=True), ("t", "y"), (6, 6 - 1)),
    ),
)
def test_select0(data, indexers, kwargs, exp_dims, exp_shape) -> None:
    *_, x = data

    result = operator.select(x, indexers=indexers, **kwargs)

    assert exp_dims == result.dims
    if isinstance(exp_shape, tuple):
        assert exp_shape == result.shape
    else:
        assert exp_shape == result.size


@MARK["issue/145"]
def test_select1(data) -> None:
    # Unpack
    *_, t_foo, t_bar, x = data

    N_y = 6

    x = genno.Quantity(x)
    assert x.size == 6 * N_y

    # Selection with inverse=False
    indexers: Mapping[Hashable, Iterable[Hashable]] = {"t": t_foo[0:1] + t_bar[0:1]}
    result_0 = operator.select(x, indexers=indexers)
    assert result_0.size == 2 * N_y
    assert result_0.name == x.name and result_0.units == x.units  # Pass through

    # Select with labels that do not appear in the data
    result_1 = operator.select(x, indexers={"t": t_foo + ["MISSING"]})
    assert result_1.size == len(t_foo) * N_y

    # Select with xarray indexers
    indexers = {
        "t": xr.DataArray(
            t_foo, dims="new_dim", coords={"new_dim": ["d1", "d2", "d3"]}
        ),
        "y": xr.DataArray(
            [2000, 2010, 2020], dims="new_dim", coords={"new_dim": ["d1", "d2", "d3"]}
        ),
    }
    # NB with pandas 2.1, this triggers the RecursionError fixed in khaeru/genno#99
    result_2 = operator.select(x, indexers)
    assert ("new_dim",) == result_2.dims

    with pytest.raises(NotImplementedError):
        operator.select(x, indexers, inverse=True)


def test_select_bigmem():
    """:func:`select` with large quantities does not exhaust memory."""
    # Create a Computer with large data
    c = Computer()
    keys = add_large_data(c, num_params=2, N_dims=17)

    # Add a task top generate random indexers
    def random_indexers(qty, *, dim_index=0, k=20):
        dims = qty.dims
        coords = qty.coords

        d = dims[dim_index]
        return {d: list(map(lambda c: c.item(), random.choices(coords[d], k=k)))}

    k = c.add("random indexers", random_indexers, keys[0])

    # Add a task to select some values
    key = c.add("test key", "select", keys[0], k)

    if genno.Quantity is SparseDataArray:
        # ValueError: invalid dims: array size defined by dims is larger than the
        # maximum possible size.
        pytest.xfail(reason="Too large for sparse")

    # Selection occurs without raising MemoryError or segfault
    result = c.get(key)

    # Result can be converted to pd.Series
    result.to_series()


def test_sub(data):
    *_, t_foo, t_bar, x = data

    # Function runs
    result = operator.sub(x, x)

    assert (0 == result).all()

    assert result.units == x.units  # Pass through


@pytest.mark.parametrize("dimensions", (["t"], ["y"], ["t", "y"]))
def test_sum(data, dimensions):
    *_, t_foo, t_bar, x = data

    # Function runs
    result = operator.sum(x, dimensions=dimensions)

    assert result.name == x.name and result.units == x.units  # Pass through


def test_unique_units_from_dim():
    # Empty quantity passes through
    q = genno.Quantity()
    r1 = operator.unique_units_from_dim(q, "foo")
    assert 0 == len(q) == len(r1)

    q = genno.Quantity(
        [[1.0, 2], [3, 4]], coords={"v": ["foo", "bar"], "u": ["kg", "km"]}, name="Baz"
    )
    with pytest.raises(
        ValueError, match=r"Non-unique units \['kg', 'km'\] for .* 'Baz'"
    ):
        operator.unique_units_from_dim(q, "u")


def test_where(data) -> None:
    *_, x = data

    value = x.sel(t="foo1", y=2020).item()

    # cond=lambda function, other=scalar
    result = operator.where(x, lambda v: v == value, 99.9)
    assert value == result.sel(t="foo1", y=2020).item()
    assert 99.9 == result.sel(t="foo2", y=2020).item()
    assert x.name == result.name
    assert x.units == result.units


def test_wildcard_qty() -> None:
    result = operator.wildcard_qty(1.0, "dimensionless", "abc")

    assert set("abc") == set(result.dims)
    assert all(c.data == ["*"] for c in result.coords.values())


def test_write_report0(tmp_path, data) -> None:
    p = tmp_path.joinpath("foo.txt")
    *_, x = data

    # Unsupported type
    with pytest.raises(NotImplementedError, match="Write <class 'list'> to file"):
        operator.write_report(list(), p)

    # Unsupported path suffix
    with pytest.raises(NotImplementedError, match="Write pandas.DataFrame to '.bar'"):
        operator.write_report(x, tmp_path.joinpath("foo.bar"))

    # Plain text
    operator.write_report("Hello, world!", p)
    assert "Hello, world!" == p.read_text()


EXP_HEADER = r"""# Hello, world!
# $
# Generated: 20..-..-..T..:..:...*$
# $
# Units: kg
# $"""


@pytest.mark.parametrize(
    "kwargs, lines",
    (
        (dict(), [1, 1]),
        (dict(header_datetime=True), [1, 1, 1, 1]),
        (dict(header_units=True), [1, 1, 0, 0, 1, 1]),
        (dict(header_datetime=True, header_units=True), [1, 1, 1, 1, 1, 1]),
    ),
)
def test_write_report1(tmp_path, data, kwargs, lines) -> None:
    *_, x = data

    # Compile the expected header
    expr = re.compile("\n".join(compress(EXP_HEADER.splitlines(), lines)), flags=re.M)

    # Header comment is written
    kwargs = dict(header_comment="Hello, world!\n") | kwargs

    # Write Quantity to CSV
    p_csv = tmp_path.joinpath("foo.csv")
    operator.write_report(x, p_csv, kwargs)
    match = expr.match(p_csv.read_text())
    assert match and 0 == match.pos

    # Write Quantity to .xlsx
    p_xlsx = tmp_path.joinpath("foo.xlsx")
    operator.write_report(x, p_xlsx, kwargs)
    assert p_xlsx.exists()

    # Write pd.DataFrame to .csv
    x_df = x.to_series().reset_index()
    p_df_csv = tmp_path.joinpath("foo from dataframe.csv")
    operator.write_report(x_df, p_df_csv, kwargs)

    # …to .xlsx
    p_df_xlsx = tmp_path.joinpath("foo from dataframe.xlsx")
    operator.write_report(x_df, p_df_xlsx, kwargs)
