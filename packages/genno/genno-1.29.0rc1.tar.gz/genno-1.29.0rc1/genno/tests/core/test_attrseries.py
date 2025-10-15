"""Tests of AttrSeries in particular."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from genno import Computer
from genno.core.attrseries import AttrSeries
from genno.testing import add_large_data


class TestAttrSeries:
    @pytest.fixture
    def foo(self):
        idx = pd.MultiIndex.from_product([["a1", "a2"], ["b1", "b2"]], names=["a", "b"])
        yield AttrSeries([0, 1, 2, 3], index=idx, name="Foo", units="kg")

    @pytest.fixture
    def bar(self):
        """A 1-dimensional quantity."""
        yield AttrSeries([0, 1], index=pd.Index(["a1", "a2"], name="a"))

    def test_align_levels(self, foo, bar):
        # Scalar vs scalar
        q = AttrSeries(0.1)
        other = AttrSeries(2.2)
        _, result = q.align_levels(other)
        assert tuple() == result.dims

        # Scalar to 1D: broadcasts to 1D
        _, result = q.align_levels(bar)
        assert ("a",) == result.dims
        assert 1 == len(result.unique())

        # Scalar to 2D:
        _, result = q.align_levels(foo)
        assert ("b",) == result.dims
        assert 1 == len(result.unique())

        # 1D to scalar
        _, result = bar.align_levels(q)
        assert ("a",) == result.dims

        # 2D vs. 2D; same dimensions, different order
        idx = pd.MultiIndex.from_product([["b1", "b2"], ["a1", "a2"]], names=["b", "a"])
        q = AttrSeries([3, 2, 1, 0], index=idx)
        assert ("b", "a") == q.dims
        _, result = q.align_levels(foo)
        assert ("a", "b") == result.dims

    def test_clip(self, foo: AttrSeries) -> None:
        with pytest.raises(NotImplementedError, match="keep_attrs=False"):
            foo.clip(1.0, keep_attrs=False)

    def test_cumprod(self, foo, bar):
        """AttrSeries.cumprod works with 1-dimensional quantities."""
        result0 = (1.1 + bar).cumprod("a")
        assert ("a",) == result0.dims

        # Same result with dim=None
        result1 = (1.1 + bar).cumprod()
        pdt.assert_series_equal(result0, result1)

        # But not with ≥1D
        with pytest.raises(NotImplementedError):
            foo.cumprod()

    def test_data(self, foo):
        assert isinstance(foo.data, np.ndarray)

    def test_expand_dims(self, ureg, foo):
        # Name and units pass through expand_dims
        result = foo.expand_dims(c=["c1", "c2"])
        assert foo.name == result.name and ureg.Unit("kg") == foo.units == result.units

    def test_interp(self, foo):
        with pytest.raises(NotImplementedError):
            foo.interp(coords=dict(a=["a1", "a1.5", "a2"], b=["b1", "b1.5", "b2"]))

    def test_rename(self, foo):
        assert foo.rename({"a": "c", "b": "d"}).dims == ("c", "d")

    def test_repr(self, foo):
        assert (
            "a   b \n"
            """a1  b1    0
    b2    1
a2  b1    2
    b2    3
Name: Foo, dtype: int64, units: kilogram"""
        ) == repr(foo)

    @pytest.mark.parametrize(
        "indexers_kwargs, dims", ((dict(a="a2"), ()), (dict(a=["a2"]), ("a",)))
    )
    def test_sel(self, bar, indexers_kwargs, dims) -> None:
        # Selecting 1 element from 1-D parameter still returns AttrSeries
        result = bar.sel(**indexers_kwargs)
        assert isinstance(result, AttrSeries)
        assert result.size == 1
        assert dims == result.dims
        assert result.iloc[0] == 1

    def test_sel_not_implemented(self, bar):
        with pytest.raises(NotImplementedError):
            bar.sel(a="a2", method="bfill")

        with pytest.raises(NotImplementedError):
            bar.sel(a="a2", tolerance=0.01)

    def test_shift(self, foo):
        foo.shift(a=1)
        foo.shift(b=1)

    def test_squeeze(self, foo) -> None:
        """:meth:`squeeze` results in MultiIndex.

        https://github.com/khaeru/genno/issues/120
        https://github.com/iiasa/message_ix/issues/788
        """
        # Squeeze the length-1 dimension "a"
        result0 = foo.sel(a=["a1"]).squeeze()

        # Result is 1-D but multi-indexed
        assert 1 == len(result0.dims)
        assert isinstance(result0.index, pd.MultiIndex)

        # Squeeze only 1 of >1 dimensions with length
        result1 = foo.sel(a=["a1"], b=["b2"]).squeeze("a")
        assert 1 == len(result1.dims)

        # Squeeze both
        result2 = foo.sel(a=["a1"], b=["b2"]).squeeze()
        assert 0 == len(result2.dims)
        result3 = foo.sel(a=["a1"], b=["b2"]).squeeze(dim=["a", "b"])
        assert 0 == len(result3.dims)

    def test_sum(self, foo, bar):
        # AttrSeries can be summed across all dimensions
        result = foo.sum(dim=["a", "b"])
        assert isinstance(result, AttrSeries)  # returns an AttrSeries
        assert result.size == 1  # with one element
        assert result.item() == 6  # that has the correct value

        # Sum with wrong dim raises ValueError
        with pytest.raises(ValueError):
            bar.sum("b")

        # Index with duplicate entries
        _baz = pd.DataFrame(
            [
                ["a1", "b1", "c1", 1.0],
                ["a1", "b1", "c1", 2.0],
                ["a2", "b2", "c3", 3.0],
                ["a2", "b2", "c4", 4.0],
                ["a3", "b3", "c5", 5.0],
            ],
            columns=["a", "b", "c", "value"],
        )
        # Fails with v1.13.0 AttrSeries.sum() using unstack()
        AttrSeries(_baz.set_index(["a", "b", "c"])["value"]).sum(dim="c")

        with pytest.raises(NotImplementedError):
            bar.sum("a", skipna=False)

    def test_others(self, foo, bar):
        # Exercise other compatibility functions
        assert type(foo.to_frame()) is pd.DataFrame
        assert foo.drop("a").dims == ("b",)
        assert bar.dims == ("a",)

        with pytest.raises(NotImplementedError):
            bar.item("a2")
        with pytest.raises(ValueError):
            bar.item()

    def test_where(self, foo: AttrSeries) -> None:
        with pytest.raises(NotImplementedError, match="drop=True"):
            foo.where(lambda x: x, drop=True)
        with pytest.raises(NotImplementedError, match="axis=….* inplace=…"):
            foo.where(lambda x: x, axis=1)
        with pytest.raises(NotImplementedError, match="axis=….* inplace=…"):
            foo.where(lambda x: x, inplace=True)


@pytest.mark.skip(reason="Slow, for benchmarking only")
def test_sum_large(N_data=1e7):  # pragma: no cover
    """Test :meth:`.AttrSeries.sum` for large, sparse data."""
    # Create a single large AttrSeries
    c = Computer()
    add_large_data(c, 1, N_dims=11, N_data=N_data)
    qty = c.get("q_00")

    # Compute a sum()
    result = qty.sum(dim=["j", "k"])
    # print(result)  # DEBUG
    del result
