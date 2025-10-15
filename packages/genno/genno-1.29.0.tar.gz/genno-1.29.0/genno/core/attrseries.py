import logging
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from functools import partial
from itertools import product, tee
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd
import pandas.core.indexes.base as ibase
import xarray as xr
from packaging.version import Version
from pandas.core.generic import NDFrame
from pandas.core.internals.base import DataManager

from genno.compat.pandas import version as pandas_version
from genno.compat.xarray import (
    Coordinates,
    DataArrayLike,
    Indexes,
    dtypes,
    either_dict_or_kwargs,
    is_scalar,
)

from .base import BaseQuantity, collect_attrs, rank, single_column_df

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparisonT

    from genno.types import Dims


log = logging.getLogger(__name__)


def _ensure_multiindex(obj):
    """Ensure `obj` has a pd.MultiIndex, even if 1D."""
    try:
        obj.index.levels  # Access an Attribute of MultiIndex that Index does not have
    except AttributeError:
        # Assign the dimension name "dim_0" if 1-D with no names
        kw = {}
        if len(obj.index) > 1 and obj.index.name is None:
            kw["names"] = ["dim_0"]
        obj.index = pd.MultiIndex.from_product([obj.index], **kw)
    else:
        # From a ≥2-dim index, drop a dimension with name `None` and only 1 level
        if len(obj.index.names) > 1 and None in obj.index.names:
            obj.index = obj.index.droplevel(obj.index.names.index(None))

    return obj


class AttrSeriesCoordinates(Coordinates):
    def __init__(self, obj):
        self._data = obj
        self._idx = obj.index.remove_unused_levels()

    @property
    def _names(self):
        return tuple(filter(None, self._idx.names))

    @property
    def variables(self):
        result = {}
        for name, levels in zip(self._idx.names, self._idx.levels):
            if name is None:
                continue
            result[name] = levels.unique()
        return result

    def __contains__(self, key: Hashable) -> bool:
        return key in self._names

    def __getitem__(self, key):
        levels = self._idx.levels[self._idx.names.index(key)].to_list()
        return xr.DataArray(levels, coords={key: levels})


class AttrSeries(BaseQuantity, pd.Series, DataArrayLike):
    """:class:`pandas.Series` subclass imitating :class:`xarray.DataArray`.

    The AttrSeries class provides similar methods and behaviour to
    :class:`xarray.DataArray`, so that :mod:`genno.operator` functions and user code can
    use xarray-like syntax. In particular, this allows such code to be agnostic about
    the order of dimensions.

    Parameters
    ----------
    units : str or pint.Unit, optional
        Set the units attribute. The value is converted to :class:`pint.Unit` and added
        to `attrs`.
    attrs : :class:`~collections.abc.Mapping`, optional
        Set the :attr:`~pandas.Series.attrs` of the AttrSeries. This attribute was added
        in `pandas 1.0 <https://pandas.pydata.org/docs/whatsnew/v1.0.0.html>`_, but is
        not currently supported by the Series constructor.
    """

    # See https://pandas.pydata.org/docs/development/extending.html
    @property
    def _constructor(self):
        return AttrSeries

    def __init__(
        self,
        data: Any = None,
        *args,
        name: Hashable | None = None,
        attrs: Mapping | None = None,
        **kwargs,
    ):
        # Emulate behaviour of Series.__init__
        if isinstance(data, DataManager) and "fastpath" not in kwargs:
            if not (
                0 == len(args) == len(kwargs) and attrs is None
            ):  # pragma: no cover
                raise NotImplementedError
            NDFrame.__init__(self, data)
            if name:
                self.name = name
            return

        attrs = collect_attrs(data, attrs, kwargs)

        if isinstance(data, (pd.Series, xr.DataArray)):
            # Extract name from existing object or use the argument
            name = ibase.maybe_extract_name(name, data, type(self))

            try:
                # Pre-convert from xr.DataArray to pd.Series to preserve names and
                # labels. For AttrSeries, this is a no-op (see below).
                data = data.to_series()
            except AttributeError:
                # pd.Series
                pass
            except ValueError:
                # xr.DataArray
                if data.shape == tuple():
                    # data is a scalar/0-dimensional xr.DataArray. Pass the 1 value
                    data = data.data
                else:  # pragma: no cover
                    raise

        data, name = single_column_df(data, name)

        if data is None:
            kwargs["dtype"] = float
        elif coords := kwargs.pop("coords", None):
            # Handle xarray-style coords arg
            data = np.array(data).ravel()
            kwargs["index"] = pd.MultiIndex.from_product(
                list(coords.values()), names=list(coords.keys())
            )

        # Don't pass attrs to pd.Series constructor; it currently does not accept them
        pd.Series.__init__(self, data, *args, name=name, **kwargs)

        # Ensure a MultiIndex
        _ensure_multiindex(self)

        # Update the attrs after initialization
        self._attrs.update(attrs)

    def __repr__(self):
        return (
            super().__repr__() + f", units: {self.attrs.get('_unit', 'dimensionless')}"
        )

    @classmethod
    def from_series(cls, series, sparse=None):
        """Like :meth:`xarray.DataArray.from_series`."""
        return AttrSeries(series)

    @staticmethod
    def _perform_binary_op(
        op, left: "AttrSeries", right: "AttrSeries", factor: float
    ) -> "AttrSeries":
        # Ensure both operands are multi-indexed, and have at least 1 common dim
        if left.dims:
            order, right = right.align_levels(left)
        else:
            order, left = left.align_levels(right)

        # Invoke a pd.Series method like .mul()
        fv = dict(fill_value=0.0) if rank(op) == 1 else {}
        # FIXME In downstream code this occasionally warns RuntimeWarning: The values
        #       in the array are unorderable. Pass `sort=False` to suppress this
        #       warning. Address.
        return getattr(left, op.__name__)(right, **fv).dropna().reorder_levels(order)

    def assign_coords(self, coords=None, **coord_kwargs):
        """Like :meth:`xarray.DataArray.assign_coords`."""
        coords = either_dict_or_kwargs(coords, coord_kwargs, "assign_coords")

        # Construct a new index
        new_idx = self.index.copy()
        for dim, values in coords.items():
            expected_len = len(self.index.levels[self.index.names.index(dim)])
            if expected_len != len(values):
                raise ValueError(
                    f"conflicting sizes for dimension {repr(dim)}: length "
                    f"{expected_len} on <this-array> and length {len(values)} on "
                    f"{repr(dim)}"
                )

            new_idx = new_idx.set_levels(values, level=dim)

        # Return a new object with the new index
        return self.set_axis(new_idx)

    def bfill(self, dim: Hashable, limit: int | None = None):
        """Like :meth:`xarray.DataArray.bfill`."""
        # TODO this likely does not work for 1-D quantities due to unstack(); test and
        #      if needed use _maybe_groupby()
        return self._replace(
            self.unstack(dim)
            .bfill(axis=1, limit=limit)
            .stack()
            .reorder_levels(self.dims),
        )

    @property
    def coords(self):
        """Like :attr:`xarray.DataArray.coords`. Read-only."""
        return AttrSeriesCoordinates(self)

    def cumprod(self, dim=None, axis=None, skipna=None, **kwargs):
        """Like :meth:`xarray.DataArray.cumprod`."""
        if axis:
            log.info(f"{self.__class__.__name__}.cumprod(…, axis=…) is ignored")
        if skipna is None:
            skipna = self.dtype == float
        if dim in (None, "..."):
            if len(self.dims) > 1:
                raise NotImplementedError("cumprod() over multiple dimensions")
            dim = self.dims[0]

        def _(s):
            # Invoke cumprod from the parent class pd.Series
            return super(pd.Series, s).cumprod(skipna=skipna, **kwargs)

        return self._replace(self._groupby_apply(dim, sorted(self.coords[dim].data), _))

    @property
    def data(self):
        return self.values

    @property
    def dims(self) -> tuple[Hashable, ...]:
        """Like :attr:`xarray.DataArray.dims`."""
        # If 0-D, the single dimension has name `None` → discard
        return tuple(filter(None, self.index.names))

    @property
    def shape(self) -> tuple[int, ...]:
        """Like :attr:`xarray.DataArray.shape`."""
        idx = self.index.remove_unused_levels()
        return tuple(len(idx.levels[i]) for i in map(idx.names.index, self.dims))

    def clip(
        self,
        min=None,
        max=None,
        *,
        keep_attrs: bool | None = None,
    ):
        """Like :meth:`.xarray.DataArray.clip`.

        :meth:`.pandas.Series.clip` has arguments named `lower` and `upper` instead of
        `min` and `max`, respectively.

        :py:`keep_attrs=False` is not implemented.
        """
        if keep_attrs is False:
            raise NotImplementedError("clip(…, keep_attrs=False)")

        if pandas_version() < Version("2.1.0"):
            return self._replace(pd.Series(self).clip(min, max))
        else:
            return super().clip(min, max)  # type: ignore [safe-super]

    def drop(self, label):
        """Like :meth:`xarray.DataArray.drop`."""
        return self.droplevel(label)

    def drop_vars(self, names: Hashable | Iterable[Hashable], *, errors: str = "raise"):
        """Like :meth:`xarray.DataArray.drop_vars`."""

        return self.droplevel(names)

    def expand_dims(
        self,
        dim: Hashable | Sequence[Hashable] | Mapping[Any, Any] | None = None,
        axis: int | Sequence[int] | None = None,
        create_index_for_new_dim: bool = True,
        **dim_kwargs: Any,
    ) -> "AttrSeries":
        """Like :meth:`xarray.DataArray.expand_dims`."""
        if axis is not None:
            raise NotImplementedError(  # pragma: no cover
                "AttrSeries.expand_dims(…, axis=…) keyword argument"
            )

        # Handle inputs. This block identical to part of xr.DataArray.expand_dims.
        if isinstance(dim, int):
            raise TypeError("dim should be Hashable or sequence/mapping of Hashables")
        elif isinstance(dim, Sequence) and not isinstance(dim, str):
            if len(dim) != len(set(dim)):
                raise ValueError("dims should not contain duplicate values.")
            dim = dict.fromkeys(dim, 1)
        elif dim is not None and not isinstance(dim, Mapping):
            dim = {dim: 1}
        _dim = either_dict_or_kwargs(dim, dim_kwargs, "expand_dims")

        if not len(_dim):
            # Nothing to do → return early
            return self.copy()

        # Assemble names → keys mapping for all added dimensions at once
        n_k = {}
        for d, value in _dim.items():
            if isinstance(value, int):
                n_k[d] = range(value)
            elif isinstance(value, (list, pd.Index)) and 0 == len(value):
                log.warning(f'Insert length-1 dimension for {{"{d}": []}}')
                n_k[d] = range(1)
            else:
                n_k[d] = value
        keys = list(product(*n_k.values()))
        names = list(n_k.keys())

        return _ensure_multiindex(
            pd.concat([self] * len(keys), keys=keys, names=names, sort=False)
        )

    def ffill(self, dim: Hashable, limit: int | None = None):
        """Like :meth:`xarray.DataArray.ffill`."""
        # TODO this likely does not work for 1-D quantities due to unstack(); test and
        #      if needed use _maybe_groupby()
        return self._replace(
            self.unstack(dim)
            .ffill(axis=1, limit=limit)
            .stack()
            .reorder_levels(self.dims),
        )

    def item(self, *args):
        """Like :meth:`xarray.DataArray.item`."""
        if len(args) and args != (None,):
            raise NotImplementedError
        elif self.size != 1:
            raise ValueError
        return self.iloc[0]

    def interp(
        self,
        coords: Mapping[Hashable, Any] | None = None,
        method: str = "linear",
        assume_sorted: bool = True,
        kwargs: Mapping[str, Any] | None = None,
        **coords_kwargs: Any,
    ):
        """Like :meth:`xarray.DataArray.interp`.

        This method works around two long-standing bugs in :mod:`pandas`:

        - `pandas-dev/pandas#25460 <https://github.com/pandas-dev/pandas/issues/25460>`_
        - `pandas-dev/pandas#31949 <https://github.com/pandas-dev/pandas/issues/31949>`_
        """
        from scipy.interpolate import interp1d

        if kwargs is None:
            kwargs = {}

        coords = either_dict_or_kwargs(coords, coords_kwargs, "interp")
        if len(coords) > 1:
            raise NotImplementedError("interp() on more than 1 dimension")

        # Unpack the dimension and levels (possibly overlapping with existing)
        dim = list(coords.keys())[0]
        levels = coords[dim]
        # Ensure a list
        if isinstance(levels, (int, float)):
            levels = [levels]

        def _flat_index(obj: AttrSeries):
            """Unpack a 1-D MultiIndex from an AttrSeries."""
            return [v[0] for v in obj.index]

        # Group by `dim` so that each level appears ≤ 1 time in `group_series`

        def _(s):
            # Work around https://github.com/pandas-dev/pandas/issues/31949
            # Location of existing values
            x = s.notna()

            # Create an interpolator from the existing values
            i = interp1d(_flat_index(s[x]), s[x], kind=method, **kwargs)

            return s.fillna(pd.Series(i(_flat_index(s[~x])), index=s[~x].index))

        result = self._groupby_apply(dim, levels, _)

        # - Restore dimension order and attributes.
        # - Select only the desired `coords`.
        return self._replace(result.reorder_levels(self.dims)).sel(coords)

    def rename(
        self,
        new_name_or_name_dict: Hashable | Mapping[Hashable, Hashable] = None,
        **names: Hashable,
    ):
        """Like :meth:`xarray.DataArray.rename`."""
        if new_name_or_name_dict is None or isinstance(new_name_or_name_dict, Mapping):
            index = either_dict_or_kwargs(new_name_or_name_dict, names, "rename")
            return self.rename_axis(index=index)
        else:
            return self._set_name(new_name_or_name_dict)

    def sel(
        self,
        indexers: Mapping[Any, Any] | None = None,
        method: str | None = None,
        tolerance=None,
        drop: bool = False,
        **indexers_kwargs: Any,
    ):
        """Like :meth:`xarray.DataArray.sel`."""
        if method is not None:
            raise NotImplementedError(f"AttrSeries.sel(…, method={method!r})")
        if tolerance is not None:
            raise NotImplementedError(f"AttrSeries.sel(…, tolerance={tolerance!r})")

        indexers = either_dict_or_kwargs(indexers, indexers_kwargs, "sel")

        if len(indexers) and all(
            isinstance(i, xr.DataArray) for i in indexers.values()
        ):
            # DataArray indexers

            # Combine indexers in a data set; dimensions are aligned
            ds = xr.Dataset(indexers)

            # All dimensions indexed
            dims_indexed = set(indexers.keys())
            # Dimensions to discard
            dims_drop = set(ds.data_vars.keys())

            # Check contents of indexers
            if any(ds.isnull().any().values()):
                raise IndexError(
                    f"Dimensions of indexers mismatch: {ds.notnull().sum()}"
                )
            elif len(ds.dims) > 1:
                raise NotImplementedError(  # pragma: no cover
                    f"map to > 1 dimensions {repr(ds.dims)} with AttrSeries.sel()"
                )

            # pd.Index object with names and levels of the new dimension to be created
            idx = ds.coords.to_index()

            # Dimensions to drop on sliced data to avoid duplicated dimensions
            drop_slice = list(dims_indexed - dims_drop)

            # Dictionary of Series to concatenate
            series = {}

            # Iterate over labels in the new dimension
            for label in idx:
                # Get a slice from the indexers corresponding to this label
                loc_ds = ds.sel({idx.name: label})

                # Assemble a key with one element for each dimension
                seq0 = [loc_ds.get(d) for d in self.dims]
                # Replace None from .get() with slice(None) or unpack a single value
                seq1 = [slice(None) if item is None else item.item() for item in seq0]

                # Use the key to retrieve 1+ integer locations; slice; store
                series[label] = self.iloc[self.index.get_locs(seq1)].droplevel(
                    drop_slice
                )

            # Rejoin to a single data frame; drop the source levels
            data = pd.concat(series, names=[idx.name]).droplevel(list(dims_drop))
        else:
            # Other indexers

            # Iterate over dimensions
            idx = []
            to_drop = set()
            for dim in self.dims:
                # Get an indexer for this dimension
                i = indexers.get(dim, slice(None))

                if is_scalar(i) and (i != slice(None)):
                    to_drop.add(dim)

                # Maybe unpack an xarray DataArray indexers, for pandas
                idx.append(i.data if isinstance(i, xr.DataArray) else i)

            # Select
            data = self.loc[tuple(idx)]

            # Only drop if not returning a scalar value
            if isinstance(data, pd.Series):
                # Drop levels where a single value was selected
                data = data.droplevel(list(to_drop & set(data.index.names)))

        # Return
        return self._replace(data)

    def shift(
        self,
        shifts: Mapping[Hashable, int] | None = None,
        fill_value: Any = None,
        **shifts_kwargs: int,
    ):
        """Like :meth:`xarray.DataArray.shift`."""
        shifts = either_dict_or_kwargs(shifts, shifts_kwargs, "shift")

        # Apply shifts one-by-one
        result = self
        for dim, periods in shifts.items():
            levels = sorted(self.coords[dim].data)

            def _(s):
                # Invoke shift from the parent class pd.Series
                return super(pd.Series, s).shift(periods=periods, fill_value=fill_value)

            result = result._groupby_apply(dim, levels, _)

        return self._replace(result)

    def sum(
        self,
        dim: "Dims" = None,
        # Signature from xarray.DataArray
        # *,
        skipna: bool | None = None,
        min_count: int | None = None,
        keep_attrs: bool | None = None,
        **kwargs: Any,
    ) -> "AttrSeries":
        """Like :meth:`xarray.DataArray.sum`."""
        if skipna is not None or min_count is not None:
            raise NotImplementedError

        if dim is Ellipsis:
            dim = []
        elif dim is None or isinstance(dim, Hashable):
            dim = list(filter(None, (dim,)))

        # Check dimensions
        bad_dims = set(dim) - set(self.index.names)
        if bad_dims:
            raise ValueError(
                f"{bad_dims} not found in array dimensions {self.index.names}"
            )

        # Create the object on which to .sum()
        return self._replace(self._maybe_groupby(dim).sum(**kwargs))

    def squeeze(self, dim=None, drop=False, axis=None):
        """Like :meth:`xarray.DataArray.squeeze`."""

        idx = self.index.remove_unused_levels()

        if isinstance(dim, Iterable) and not isinstance(dim, str):
            dim = list(dim)
        elif dim is not None:
            dim = [dim]

        to_drop = []
        for i, name in enumerate(filter(None, idx.names)):
            if dim and name not in dim:
                continue
            elif len(idx.levels[i]) > 1:
                if dim is None:
                    continue
                else:
                    raise ValueError(
                        "cannot select a dimension to squeeze out which has length "
                        "greater than one"
                    )

            to_drop.append(name)

        if dim and not to_drop:
            raise KeyError(dim)  # Specified dimension does not exist

        if set(to_drop) == set(self.dims):
            # Dropping all dimensions → 0-D quantity; simply reset
            return self.reset_index(drop=True)
        else:
            return self.droplevel(to_drop).pipe(_ensure_multiindex)

    def transpose(self, *dims):
        """Like :meth:`xarray.DataArray.transpose`."""
        return self.reorder_levels(dims)

    def to_dataframe(
        self,
        name: Hashable | None = None,
        dim_order: Sequence[Hashable] | None = None,
    ) -> pd.DataFrame:
        """Like :meth:`xarray.DataArray.to_dataframe`."""
        if dim_order is not None:
            raise NotImplementedError("dim_order arg to to_dataframe()")

        self.name = name or self.name or "value"
        return self.to_frame()

    def to_series(self):
        """Like :meth:`xarray.DataArray.to_series`."""
        return self

    def where(
        self,
        cond: Any,
        other: Any = dtypes.NA,
        drop: bool = False,
        *,
        axis=None,  # Needed internally to pd.Series.clip()
        inplace: bool = False,  # Needed internally to pd.Series.clip()
    ):
        """Like :meth:`xarray.DataArray.where`.

        Passing :any:`True` for `drop` is not implemented.
        """
        if drop is True:
            raise NotImplementedError("where(…, drop=True)")
        elif axis is not None or inplace is not False:
            raise NotImplementedError("where(…, axis=…) or where(…, inplace=…)")
        return super().where(cond, other)  # type: ignore [safe-super]

    @property
    def xindexes(self):  # pragma: no cover
        # NB incomplete implementation; currently sufficient that this property exists
        return Indexes(dict(), None)

    # Internal methods
    def align_levels(
        self, other: "AttrSeries"
    ) -> tuple[Sequence[Hashable], "AttrSeries"]:
        """Return a copy of `self` with ≥1 dimension(s) in the same order as `other`.

        Work-around for https://github.com/pandas-dev/pandas/issues/25760 and other
        limitations of :class:`pandas.Series`.
        """
        # Union of dimensions of `self` and `other`; initially just other
        d_union = list(other.dims)

        # Lists of common dimensions, and dimensions on `other` missing from `self`.
        d_common = []  # Common dimensions of `self` and `other`
        d_other_only = []  # (dimension, index) of `other` missing from `self`
        for i, d in enumerate(d_union):
            if d in self.index.names:
                d_common.append(d)
            else:
                d_other_only.append((d, i))

        result = self
        d_result = []  # Order of dimensions on the result

        if len(d_common) == 0:
            # No common dimensions between `other` and `self`
            if len(d_other_only):
                # …but `other` is ≥1D
                # Broadcast the result over the final missing dimension of `other`
                d, i = d_other_only[-1]
                result = result.expand_dims({d: other.index.levels[i]})
                # Reordering starts with this dimension
                d_result.append(d)
            elif not result.dims:
                # Both `self` and `other` are scalar
                d_result.append(None)
        else:
            # Some common dimensions exist; no need to broadcast, only reorder
            d_result.extend(d_common)

        # Append the dimensions of `self`
        i1, i2 = tee(filter(lambda n: n not in other.dims, self.dims), 2)
        d_union.extend(i1)
        d_result.extend(i2)

        return d_union or [None], result.reorder_levels(d_result or [None])

    def _groupby_apply(
        self,
        dim: Hashable,
        levels: Iterable["SupportsRichComparisonT"],
        func: Callable[["AttrSeries"], "AttrSeries"],
    ) -> "AttrSeries":
        """Group along `dim`, ensure levels `levels`, and apply `func`.

        `func` should accept and return AttrSeries. The resulting AttrSeries are
        concatenated again along `dim`.
        """
        # Preserve order of dimensions
        dims = self.dims

        # Dimension other than `dim`
        d_other = list(filter(lambda d: d != dim, dims))

        def _join(base, item):
            """Rejoin a full key for the MultiIndex in the correct order."""
            # Wrap a scalar `base` (only occurs with len(other_dims) == 1; pandas < 2.0)
            base = list(base) if isinstance(base, tuple) else [base]
            return [(base[d_other.index(d)] if d in d_other else item[0]) for d in dims]

        # Grouper or iterable of (key, pd.Series)
        groups = self.groupby(d_other) if len(d_other) else [(None, self)]

        # Iterate over groups, accumulating modified series
        result = []
        for group_key, group_series in groups:
            # Work around https://github.com/pandas-dev/pandas/issues/25460; can't do:
            # group_series.reindex(…, level=dim)

            # Create 1-D MultiIndex for `dim` with the union of existing coords and
            # `levels`
            _levels = set(levels)
            _levels.update(group_series.index.get_level_values(dim))
            idx = pd.MultiIndex.from_product([sorted(_levels)], names=[dim])
            # Reassemble full MultiIndex with the new coords added along `dim`
            full_idx = pd.MultiIndex.from_tuples(
                map(partial(_join, group_key), idx), names=dims
            )

            # - Reindex with `full_idx` to insert NaNs for new `levels`.
            # - Replace the with the 1D index for `dim` only.
            # - Apply `func`.
            # - Restore the full index.
            result.append(
                func(group_series.reindex(full_idx).set_axis(idx)).set_axis(full_idx)
            )

        return pd.concat(result)

    def _maybe_groupby(self, dim):
        """Return an object for operations along dimension(s) `dim`.

        If `dim` is a subset of :attr:`dims`, returns a SeriesGroupBy object along the
        other dimensions.
        """
        if len(set(dim)) in (0, len(self.index.names)):
            return cast(pd.Series, super())
        else:
            # Group on dimensions other than `dim`
            levels = list(filter(lambda d: d not in dim, self.index.names))
            return self.groupby(level=levels, group_keys=False, observed=True)

    def _replace(self, data) -> "AttrSeries":
        """Shorthand to preserve attrs."""
        return self.__class__(data, name=self.name, attrs=self.attrs)
