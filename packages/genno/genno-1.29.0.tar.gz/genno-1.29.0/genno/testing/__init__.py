import contextlib
import importlib.resources
import logging
import os
import platform
from contextlib import nullcontext
from functools import partial
from importlib.metadata import version
from itertools import chain, islice
from typing import TYPE_CHECKING, ContextManager

import numpy as np
import pandas as pd
import pint
import pytest
import xarray as xr
import xarray.testing
from dask.core import quote
from pandas.testing import assert_series_equal

import genno
from genno import ComputationError, Computer, Key, set_class
from genno.compat.pint import PintError
from genno.core.attrseries import AttrSeries
from genno.core.sparsedataarray import HAS_SPARSE, SparseDataArray

if TYPE_CHECKING:
    from genno.core.quantity import AnyQuantity


log = logging.getLogger(__name__)

GHA = "GITHUB_ACTIONS" in os.environ

# Common marks used in multiple places. Do not reuse keys.
MARK = {
    "issue/145": pytest.mark.xfail(
        condition="2024.10.0" <= version("xarray"),
        reason="with SparseDataArray only (https://github.com/pydata/xarray/issues/9694)",
    ),
    "jupyter_client#1079": pytest.mark.skipif(
        condition=platform.python_version_tuple() >= ("3", "14", "0"),
        reason="https://jupyter/jupyter_client/issues/1079",
    ),
}

# Pytest hooks


def pytest_configure(config):
    """Force iam-units to use a distinct cache for each worker.

    Work arounds for:

    1. https://github.com/hgrecco/flexcache/issues/6 and
       https://github.com/IAMconsortium/units/issues/54.
    2. https://github.com/python/cpython/issues/125235,
       https://github.com/astral-sh/uv/issues/7036, or similar.
    """
    name = f"iam-units-{os.environ.get('PYTEST_XDIST_WORKER', '')}".rstrip("-")
    os.environ["IAM_UNITS_CACHE"] = str(config.cache.mkdir(name))

    if GHA and platform.system() == "Windows":
        import matplotlib

        matplotlib.use("agg")


def pytest_sessionstart(session):
    """Quiet some loggers."""
    for name in (
        "numba",
        "matplotlib.backends",
        "matplotlib.font_manager",
        "PIL.PngImagePlugin",
    ):
        logging.getLogger(name).setLevel(logging.INFO)


def pytest_runtest_makereport(item, call):
    """Pytest hook to unwrap :class:`genno.ComputationError`.

    This allows to "xfail" tests more precisely on the underlying exception, rather than
    the ComputationError which wraps it.
    """
    if call.when == "call" and getattr(call.excinfo, "type", None) is ComputationError:
        # Retrieve the Exception wrapped by ComputationError
        e = call.excinfo.value.args[0]
        # Look for an "xfail" marker whose raises= class(es) match `e`
        for mark in filter(
            lambda m: m.name == "xfail" and isinstance(e, m.kwargs.get("raises", ())),
            item.iter_markers(),
        ):
            # Change the ExceptionInfo describe `e`, which will match this mark
            # and produce an "xfail" report
            call.excinfo = pytest.ExceptionInfo(
                excinfo=(type(e), e, e.__traceback__), _ispytest=True
            )

            # Generate and return the report
            return pytest.TestReport.from_item_and_call(item, call)


def add_large_data(c: Computer, num_params, N_dims=6, N_data=0):
    """Add nodes to `c` that return large-ish data.

    The result is a matrix wherein the Cartesian product of all the keys is very large—
    about 2e17 elements for N_dim = 6—but the contents are very sparse. This can be
    handled by :class:`.SparseDataArray`, but not by :class:`xarray.DataArray` backed
    by :class:`numpy.ndarray`.
    """

    def _fib():
        """Yield dimensions and their lengths: Fibonacci numbers."""
        a, b = 233, 377
        dim_names = iter("abcdefghijklmnopqrstuvwxyz")
        yield next(dim_names), a
        while True:
            yield next(dim_names), b
            a, b = b, a + b

    # Dimensions and their lengths
    dims, sizes = zip(*islice(_fib(), N_dims))
    # Number of data points to generate
    N_data = max(int(N_data), sizes[-1])

    # commented; for debugging
    # # Output something like "True: 2584 values / 2.182437e+17 = 1.184e-12% full"
    # from math import prod
    #
    # total = prod(sizes)
    # log.info(
    #     # See https://github.com/pydata/sparse/issues/429; total elements must be
    #     # less than the maximum value of np.intp
    #     repr(total < np.iinfo(np.intp).max)
    #     + f": {max(sizes)} values / {total:3e} = {100 * max(sizes) / total:.3e}% full"
    # )

    # Names like f_00000 ... f_01596 along each dimension
    dtypes = {"value": float}
    for d, N in zip(dims, sizes):
        categories = [f"{d}_{i:05d}" for i in range(N)]
        # Add to Computer
        c.add(d, quote(categories))
        # Create a categorical dtype
        dtypes[d] = pd.CategoricalDtype(categories)

    # Random generator
    rng = np.random.default_rng()

    def get_large_quantity(name):
        """Make a DataFrame containing each label in *coords* ≥ 1 time."""
        log.info(f"{N_data} values")

        # Allocate memory for the data frame using the given data types
        df = pd.DataFrame(
            index=pd.RangeIndex(N_data), columns=list(dims) + ["value"]
        ).astype(dtypes)

        # Fill values
        df.loc[:, "value"] = rng.random(N_data)

        # Fill labels
        for d in dims:
            df[d] = pd.Categorical.from_codes(
                rng.integers(0, len(dtypes[d].categories), N_data), dtype=dtypes[d]
            )

        return genno.Quantity(
            df.set_index(list(dims)),
            units=pint.get_application_registry().kilogram,
            name=name,
        )

    # Fill the Scenario with quantities named q_01 ... q_09
    keys = []
    for i in range(num_params):
        key = Key(f"q_{i:02d}", dims)
        c.add(key, (partial(get_large_quantity, key),))
        keys.append(key)

    return keys


def add_test_data(c: Computer):
    """:func:`add_test_data` operating on a Computer, not an ixmp.Scenario."""
    # TODO combine with add_dantzig(), below
    # New sets
    t_foo = ["foo{}".format(i) for i in (1, 2, 3)]
    t_bar = ["bar{}".format(i) for i in (4, 5, 6)]
    t = t_foo + t_bar
    y = list(range(2000, 2051, 10))

    # Add to Computer
    c.add("t", quote(t))
    c.add("y", quote(y))

    # Data
    ureg = pint.get_application_registry()
    x = genno.Quantity(
        np.random.rand(len(t), len(y)),
        coords={"t": t, "y": y},
        units=ureg.kg,
        name="Quantity X",
    )

    # Add, including sums and to index
    c.add(Key("x", ("t", "y")), genno.Quantity(x), sums=True)

    return t, t_foo, t_bar, x


_i = ["seattle", "san-diego"]
_j = ["new-york", "chicago", "topeka"]
_TEST_DATA = {
    Key(k): data
    for k, data in {
        "a:i": (xr.DataArray([350, 600], coords=[("i", _i)]), "cases"),
        "b:j": (xr.DataArray([325, 300, 275], coords=[("i", _j)]), "cases"),
        "d:i-j": (
            xr.DataArray(
                [[2.5, 1.7, 1.8], [2.5, 1.8, 1.4]], coords=[("i", _i), ("j", _j)]
            ),
            "km",
        ),
        "f:": (90.0, "USD/km"),
        # TODO complete the following
        # Decision variables and equations
        "x:i-j": (
            xr.DataArray([[0, 0, 0], [0, 0, 0]], coords=[("i", _i), ("j", _j)]),
            "cases",
        ),
        "z:": (0, "cases"),
        "cost:": (0, "USD"),
        "cost-margin:": (0, "USD"),
        "demand:j": (xr.DataArray([0, 0, 0], coords=[("j", _j)]), "cases"),
        "demand-margin:j": (xr.DataArray([0, 0, 0], coords=[("j", _j)]), "cases"),
        "supply:i": (xr.DataArray([0, 0], coords=[("i", _i)]), "cases"),
        "supply-margin:i": (xr.DataArray([0, 0], coords=[("i", _i)]), "cases"),
    }.items()
}


def get_test_quantity(key: Key) -> "AnyQuantity":
    """Computation that returns test data."""
    value, unit = _TEST_DATA[key]
    return genno.Quantity(value, name=key.name, units=unit)


def add_dantzig(c: Computer):
    """Add contents analogous to the ixmp Dantzig scenario."""

    c.add("i", quote(_i))
    c.add("j", quote(_j))

    _all = list()
    for key in _TEST_DATA.keys():
        c.add(key, (partial(get_test_quantity, key),), sums=True)
        _all.append(key)

    c.add("all", sorted(_all))


@contextlib.contextmanager
def assert_logs(caplog, message_or_messages=None, at_level=None):
    """Assert that *message_or_messages* appear in logs.

    Use assert_logs as a context manager for a statement that is expected to trigger
    certain log messages. assert_logs checks that these messages are generated.

    Derived from :func:`ixmp.testing.assert_logs`.

    Example
    -------
    >>> def test_foo(caplog):
    ...     with assert_logs(caplog, 'a message'):
    ...         logging.getLogger(__name__).info('this is a message!')

    Parameters
    ----------
    caplog : object
        The pytest caplog fixture.
    message_or_messages : str or list of str
        String(s) that must appear in log messages.
    at_level : int, optional
        Messages must appear on 'genno' or a sub-logger with at least this level.
    """
    __tracebackhide__ = True

    # Wrap a string in a list
    expected = (
        [message_or_messages]
        if isinstance(message_or_messages, str)
        else message_or_messages
    )

    # Record the number of records prior to the managed block
    first = len(caplog.records)

    if at_level is not None:
        # Use the pytest caplog fixture's built-in context manager to temporarily set
        # the level of the logger for the whole package (parent of the current module)
        ctx = caplog.at_level(at_level, logger=__name__.split(".")[0])
    else:
        # ctx does nothing
        ctx = contextlib.nullcontext()

    try:
        with ctx:
            yield  # Nothing provided to the managed block
    finally:
        # List of bool indicating whether each of `expected` was found
        found = [any(e in msg for msg in caplog.messages[first:]) for e in expected]

        if not all(found):
            # Format a description of the missing messages
            lines = chain(
                ["Did not log:"],
                [f"    {repr(msg)}" for i, msg in enumerate(expected) if not found[i]],
                ["among:"],
                ["    []"]
                if len(caplog.records) == first
                else [f"    {repr(msg)}" for msg in caplog.messages[first:]],
            )
            pytest.fail("\n".join(lines))


def assert_qty_equal(
    a,
    b,
    check_type: bool = True,
    check_attrs: bool = True,
    ignore_extra_coords: bool = False,
    **kwargs,
):
    """Assert that objects `a` and `b` are equal.

    Parameters
    ----------
    check_type : bool, optional
        Assert that `a` and `b` are both :class:`.Quantity` instances. If :obj:`False`,
        the arguments are converted to Quantity.
    check_attrs : bool, optional
        Also assert that check that attributes are identical.
    ignore_extra_coords : bool, optional
        Ignore extra coords that are not dimensions. Only meaningful when Quantity is
        :class:`.SparseDataArray`.
    """
    __tracebackhide__ = True

    try:
        assert type(a) is type(b) is genno.Quantity
    except AssertionError:
        if check_type:
            raise
        else:
            # Convert both arguments to Quantity
            a = genno.Quantity(a)
            b = genno.Quantity(b)

    if genno.Quantity is AttrSeries:
        try:
            a = a.sort_index().dropna()
            b = b.sort_index().dropna()
        except TypeError:  # pragma: no cover
            pass
        assert_series_equal(a, b, check_dtype=False, **kwargs)
    else:
        import xarray.testing

        if ignore_extra_coords:  # pragma: no cover
            a = a.reset_coords(set(a.coords.keys()) - set(a.dims), drop=True)
            b = b.reset_coords(set(b.coords.keys()) - set(b.dims), drop=True)

        assert 0 == len(kwargs)

        xarray.testing.assert_equal(a._sda.dense, b._sda.dense)

    # Check attributes are equal
    if check_attrs:
        assert a.attrs == b.attrs


def assert_qty_allclose(
    a,
    b,
    check_type: bool = True,
    check_attrs: bool = True,
    ignore_extra_coords: bool = False,
    **kwargs,
):
    """Assert that objects `a` and `b` have numerically close values.

    Parameters
    ----------
    check_type : bool, optional
        Assert that `a` and `b` are both :class:`.Quantity` instances. If :obj:`False`,
        the arguments are converted to Quantity.
    check_attrs : bool, optional
        Also assert that check that attributes are identical.
    ignore_extra_coords : bool, optional
        Ignore extra coords that are not dimensions. Only meaningful when Quantity is
        :class:`.SparseDataArray`.
    """
    __tracebackhide__ = True

    try:
        assert type(a) is type(b) is genno.Quantity
    except AssertionError:
        if check_type:
            raise
        else:
            # Convert both arguments to Quantity
            a = genno.Quantity(a)
            b = genno.Quantity(b)

    if genno.Quantity is AttrSeries:
        assert_series_equal(a.sort_index(), b.sort_index(), **kwargs)
    else:
        if ignore_extra_coords:
            a = a.reset_coords(set(a.coords.keys()) - set(a.dims), drop=True)
            b = b.reset_coords(set(b.coords.keys()) - set(b.dims), drop=True)

        # Remove a kwarg not recognized by the xarray function
        kwargs.pop("check_dtype", None)

        xarray.testing.assert_allclose(a._sda.dense, b._sda.dense, **kwargs)

    # Check attributes are equal
    if check_attrs:
        assert a.attrs == b.attrs


def assert_units(qty: "AnyQuantity", exp: str) -> None:
    """Assert that `qty` has units `exp`."""
    assert (qty.units / qty.units._REGISTRY(exp)).dimensionless, (
        f"Units '{qty.units:~}'; expected {repr(exp)}"
    )


def raises_or_warns(value, *args, **kwargs) -> ContextManager:
    """Context manager for tests that :func:`.pytest.raises` or :func:`.pytest.warns`.

    If `value` is a context manager—such as returned by :func:`.pytest.raises`, it is
    used directly.

    Examples
    --------
    .. code-block:: python

       @pytest.mark.parametrize(
           "input, output", (("FOO", 1), ("BAR", pytest.raises(ValueError)))
       )
       def test_myfunc0(input, expected):
           with raises_or_warns(expected, DeprecationWarning, match="FOO"):
               assert expected == myfunc(input)

    In this example:

    - :py:`myfunc("FOO")` is expected to emit :class:`DeprecationWarning` and return 1.
    - :py:`myfunc("BAR")` is expected to raise :class:`ValueError` and issue no warning.

    .. code-block:: python

       @pytest.mark.parametrize(
           "input, output", (("FOO", 1), ("BAR", pytest.raises(ValueError)))
       )
       def test_myfunc1(input, expected):
           with raises_or_warns(expected, None):
               assert expected == myfunc(input)

    In this example, no warnings are expected from :py:`myfunc("FOO")`.
    """
    if isinstance(value, ContextManager):
        return value
    elif args == (None,) and kwargs == {}:
        return nullcontext()
    else:
        return pytest.warns(*args, **kwargs)


# Fixtures


@pytest.fixture(scope="session")
def test_data_path():
    """Path to the directory containing test data."""
    return importlib.resources.files("genno.tests.data")


@pytest.fixture(scope="session")
def ureg():
    """Application-wide units registry."""
    registry = pint.get_application_registry()

    # Used by .compat.ixmp, .compat.pyam
    for name in ("USD", "case"):
        try:
            registry.define(f"{name} = [{name}]")
        except PintError:  # pragma: no cover
            # pint.RedefinitionError with pint 0.22 on Python ≤ 3.11
            # pint.DefinitionSyntaxError with pint 0.17 on Python 3.12
            pass

    yield registry


@pytest.fixture(
    params=[
        (True, "AttrSeries", AttrSeries),
        (HAS_SPARSE, "SparseDataArray", SparseDataArray),
    ],
    ids=["attrseries", "sparsedataarray"],
)
def parametrize_quantity_class(request):
    """Fixture to run tests twice, for both Quantity implementations."""
    from genno.core import quantity

    if not request.param[0]:  # pragma: no cover
        pytest.skip(reason="`sparse` not available → can't test SparseDataArray")

    pre = quantity.CLASS

    try:
        set_class(request.param[1])
        yield
    finally:
        set_class(pre)


@pytest.fixture(params=[True, False], ids=["cow-true", "cow-false"])
def parametrize_copy_on_write(monkeypatch, request):
    """Fixture to run tests with pandas copy-on-write either enabled or disabled."""
    monkeypatch.setattr(pd.options.mode, "copy_on_write", request.param)
    yield


@pytest.fixture(scope="function")
def quantity_is_sparsedataarray(request):
    from genno.core import quantity

    pre = quantity.CLASS

    try:
        set_class("SparseDataArray")
        yield
    finally:
        set_class(pre)


def __getattr__(name):
    if name == "random_qty":
        from warnings import warn

        warn(
            "Import random_qty from genno.testing; import from genno.operator instead",
            DeprecationWarning,
            stacklevel=2,
        )

        from genno.operator import random_qty

        return random_qty
    raise AttributeError(name)
