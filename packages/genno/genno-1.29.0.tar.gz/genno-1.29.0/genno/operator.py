"""Elementary operators for genno."""

# NB To avoid ambiguity, operators should not have default values for positional-only
#    arguments; use keyword(-only) arguments for defaults.
import logging
import operator
import os
import re
from collections.abc import Callable, Collection, Hashable, Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from functools import partial, reduce, singledispatch
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd
import pint
import xarray as xr

import genno

from .compat.xarray import dtypes, either_dict_or_kwargs, is_scalar
from .core.attrseries import AttrSeries
from .core.key import Key, KeyLike, iter_keys, single_key
from .core.operator import Operator
from .core.quantity import assert_quantity
from .core.sparsedataarray import SparseDataArray
from .util import collect_units, filter_concat_args, units_with_multiplier

if TYPE_CHECKING:
    from genno import types

    from .types import AnyQuantity, TQuantity, UnitLike

__all__ = [
    "add",
    "aggregate",
    "apply_units",
    "as_quantity",
    "assign_units",
    "broadcast_map",
    "clip",
    "combine",
    "concat",
    "convert_units",
    "disaggregate_shares",
    "div",
    "drop_vars",
    "expand_dims",
    "group_sum",
    "index_to",
    "interpolate",
    "load_file",
    "mul",
    "pow",
    "product",
    "random_qty",
    "ratio",
    "relabel",
    "rename",
    "rename_dims",
    "round",
    "select",
    "sub",
    "sum",
    "unique_units_from_dim",
    "where",
    "wildcard_qty",
    "write_report",
]

log = logging.getLogger(__name__)


# Carry unit attributes automatically
xr.set_options(keep_attrs=True)


def add_binop(func, c: "genno.Computer", key, *quantities, **kwargs) -> Key:
    """:meth:`.Computer.add` helper for binary operations.

    Add a computation that applies :func:`.add`, :func:`.div`, :func:`.mul`, or
    :func:`.sub` to `quantities`.

    Parameters
    ----------
    key : str or .Key
        Key or name of the new quantity. If a Key, any dimensions are ignored; the
        dimensions of the result are the union of the dimensions of `quantities`.
    sums : bool, optional
        If :obj:`True`, all partial sums of the new quantity are also added.

    Returns
    -------
    .Key
        The full key of the new quantity.

    Example
    -------
    >>> c = Computer()
    >>> x = c.add("x:a-b-c", ...)
    >>> y = c.add("y:c-d-e", ...)
    >>> z = c.add("z", "mul", x, y)
    >>> z
    <z:a-b-c-d-e>
    """
    # Fetch the full key for each quantity
    base_keys = c.check_keys(
        *quantities, predicate=lambda v: isinstance(v, (genno.Quantity, int, float))
    )

    # Compute a key for the result
    # Parse the name and tag of the target
    key = Key(key)

    # New key with dimensions of the product
    candidate = Key.product(key.name, *base_keys, tag=key.tag)
    # Only use this if it has greater dimensionality than `key`
    if set(candidate.dims) >= set(key.dims):
        key = candidate

    # Add the basic result to the graph and index
    kwargs.setdefault("sums", True)
    keys = iter_keys(c.add(key, func, *base_keys, **kwargs))

    return next(keys) if kwargs["sums"] else single_key(keys)


@Operator.define(helper=add_binop)
def add(*quantities: "TQuantity", fill_value: float = 0.0) -> "TQuantity":
    """Sum across multiple `quantities`.

    Raises
    ------
    ValueError
        if any of the `quantities` have incompatible units.

    Returns
    -------
    .Quantity
        Units are the same as the first of `quantities`.

    See also
    --------
    add_binop
    """
    # Ensure arguments are all quantities
    assert_quantity(*quantities)

    return reduce(operator.add, quantities[1:], quantities[0])


def aggregate(
    quantity: "TQuantity", groups: Mapping[str, Mapping], keep: bool
) -> "TQuantity":
    """Aggregate `quantity` by `groups`.

    Parameters
    ----------
    groups: dict of dict
        Top-level keys are the names of dimensions in `quantity`. Second-level keys are
        group names; second-level values are lists of labels along the dimension to sum
        into a group. Labels may be literal values, or compiled :class:`re.Pattern`
        objects; in the latter case, all matching labels (according to
        :meth:`re.Pattern.fullmatch`) are included in the group to be aggregated.
    keep : bool
        If True, the members that are aggregated into a group are returned with the
        group sums. If False, they are discarded.

    Returns
    -------
    :class:`.Quantity`
        Same dimensionality as `quantity`.
    """
    result = quantity

    for dim, dim_groups in groups.items():
        # Optionally keep the original values
        values = [result] if keep else []

        # This raises a spurious warning from numpy; see filter in pyproject.toml
        coords = result.coords[dim].data

        # Aggregate each group
        for group, members in dim_groups.items():
            if keep and group in coords:
                log.warning(
                    f"{dim}={group!r} is already present in quantity {quantity.name!r} "
                    "with keep=True"
                )

            # Handle regular expressions in `members`; skip items not in `coords`
            mem: list[Hashable] = []
            for m in members:
                if isinstance(m, re.Pattern):
                    mem.extend(filter(m.fullmatch, coords))
                elif m in coords:
                    mem.append(m)

            # Select relevant members; sum along `dim`; label with the `group` ID
            agg = result.sel({dim: mem}).sum(dim=dim).expand_dims({dim: [group]})

            if isinstance(agg, AttrSeries):
                # .transpose() is necessary for AttrSeries
                agg = agg.transpose(*quantity.dims)
            else:
                # Restore fill_value=NaN for compatibility
                agg = agg._sda.convert()
            values.append(agg)

        # Reassemble to a single dataarray
        result = concat(
            *values, **({} if isinstance(quantity, AttrSeries) else {"dim": dim})
        )

    return quantity._keep(result, name=True, attrs=True)


def _unit_args(qty, units):
    result = [pint.get_application_registry(), qty.attrs.get("_unit", None)]
    return *result, getattr(result[1], "dimensionality", {}), result[0].Unit(units)


def apply_units(qty: "TQuantity", units: "UnitLike") -> "TQuantity":
    """Apply `units` to `qty`.

    If `qty` has existing units…

    - …with compatible dimensionality to `units`, the magnitudes are adjusted, i.e.
      behaves like :func:`convert_units`.
    - …with incompatible dimensionality to `units`, the units attribute is overwritten
      and magnitudes are not changed, i.e. like :func:`assign_units`, with a log message
      on level ``WARNING``.

    To avoid ambiguities between the two cases, use :func:`convert_units` or
    :func:`assign_units` instead.

    Parameters
    ----------
    units : str or pint.Unit
        Units to apply to `qty`.
    """
    registry, existing, existing_dims, new_units = _unit_args(qty, units)

    if len(existing_dims):
        # Some existing dimensions: log a message either way
        if existing_dims == new_units.dimensionality:
            log.debug(f"Convert '{existing}' to '{new_units}'")
            # NB use a factor because pint.Quantity cannot wrap AttrSeries
            result = qty * registry.Quantity(1.0, existing).to(new_units).magnitude
        else:
            log.warning(f"Replace '{existing}' with incompatible '{new_units}'")
            result = qty.copy()
    else:
        # No units, or dimensionless
        result = qty.copy()

    return qty._keep(result, name=True, attrs=True, units=new_units)


def as_quantity(info: dict | float | str) -> "AnyQuantity":
    """Convert various values to Quantity.

    This operator can be useful when handling values from user input or various file
    formats.

    Examples
    --------
    :class:`str`, via :mod:`pint`:

    >>> as_quantity("3.0 kg")

    :class:`dict`:

    - A ‘_dim’ key is removed and treated as :attr:`Quantity.dims`.
    - A ‘_unit’ key is removed and treated as :attr:`Quantity.units`.

    >>> value = {
    ...     ("x0", "y0"): 1.0,
    ...     ("x1", "y1"): 2.0,
    ...     "_dim": ("x", "y"),
    ...     "_unit": "km",
    ... }
    >>> as_quantity(value)

    For other values, the :class:`Quantity` constructor should be used directly:

    >>> Quantity(1.2)

    """
    if isinstance(info, str):
        import pint

        registry = pint.get_application_registry()
        q = registry.Quantity(info)
        return genno.Quantity(q.magnitude, units=q.units)
    elif isinstance(info, dict):
        data = info.copy()
        dim = data.pop("_dim")
        unit = data.pop("_unit")
        return genno.Quantity(pd.Series(data).rename_axis(dim), units=unit)
    elif isinstance(info, (float, int)):
        log.info(f"Can use Quantity(…) directly for {type(info)} input")
        return genno.Quantity(info)
    else:
        raise TypeError(type(info))


def assign_units(qty: "TQuantity", units: "UnitLike") -> "TQuantity":
    """Set the `units` of `qty` without changing magnitudes.

    Logs on level ``INFO`` if `qty` has existing units.

    Parameters
    ----------
    units : str or pint.Unit
        Units to assign to `qty`.
    """
    registry, existing, existing_dims, new_units = _unit_args(qty, units)

    if len(existing_dims):
        msg = f"Replace '{existing}' with '{new_units}'"
        # Some existing dimensions: log a message either way
        if existing_dims == new_units.dimensionality:
            # NB use a factor because pint.Quantity cannot wrap AttrSeries
            if registry.Quantity(1.0, existing).to(new_units).magnitude != 1.0:
                log.info(f"{msg} without altering magnitudes")
        else:
            log.info(f"{msg} with different dimensionality")

    result = qty.copy()
    result.units = new_units

    return result


def broadcast_map(
    quantity: "TQuantity",
    map: "TQuantity",
    rename: Mapping = {},
    strict: bool = False,
) -> "TQuantity":
    """Broadcast `quantity` using a `map`.

    The `map` must be a 2-dimensional Quantity with dimensions (``d1``, ``d2``), such as
    returned by :func:`ixmp.report.operator.map_as_qty`. `quantity` must also have a
    dimension ``d1``. Typically ``len(d2) > len(d1)``.

    `quantity` is 'broadcast' by multiplying it with `map`, and then summing on the
    common dimension ``d1``. The result has the dimensions of `quantity`, but with
    ``d2`` in place of ``d1``.

    Parameters
    ----------
    rename : dict, optional
        Dimensions to rename on the result; mapping from original dimension
        (:class:`str`) to target name (:class:`str`).
    strict : bool, optional
        Require that each element of ``d2`` is mapped from exactly 1 element of ``d1``.
    """
    if strict and int(map.sum().item()) != len(map.coords[map.dims[1]]):
        raise ValueError("invalid map")

    return product(quantity, map).sum([map.dims[0]]).rename(rename)


def clip(
    qty: "TQuantity",
    min: "types.ScalarOrArray | None" = None,
    max: "types.ScalarOrArray | None" = None,
    *,
    keep_attrs: bool | None = None,
) -> "TQuantity":
    """Call :meth:`.Quantity.clip`."""
    return qty.clip(min, max, keep_attrs=keep_attrs)


def combine(
    *quantities: "TQuantity",
    select: list[Mapping] | None = None,
    weights: list[float] | None = None,
) -> "TQuantity":  # noqa: F811
    """Sum distinct `quantities` by `weights`.

    Parameters
    ----------
    *quantities : .Quantity
        The quantities to be added.
    select : list of dict
        Elements to be selected from each quantity. Must have the same number of
        elements as `quantities`.
    weights : list of float
        Weight applied to each quantity. Must have the same number of elements as
        `quantities`.

    Raises
    ------
    ValueError
        If the `quantities` have mismatched units.
    """
    # Handle arguments
    if select is None:
        select = [{}] * len(quantities)
    weights = weights or len(quantities) * [1.0]

    # Check units
    units = collect_units(*quantities)
    for u in units:
        # TODO relax this condition: modify the weights with conversion factors if the
        #      units are compatible, but not the same
        if u != units[0]:
            raise ValueError(f"Cannot combine() units {units[0]} and {u}")
    units = units[0]

    args = []

    for quantity, indexers, weight in zip(quantities, select, weights):
        # Select data
        temp = globals()["select"](quantity, indexers)

        # Dimensions along which multiple values are selected
        multi = [dim for dim, values in indexers.items() if isinstance(values, list)]
        if len(multi):
            # Sum along these dimensions
            temp = temp.sum(dim=multi)

        args.append(weight * temp)

    result = add(*args)
    result.units = units

    return result


@singledispatch
def concat(*objs: "TQuantity", **kwargs) -> "TQuantity":
    """Concatenate Quantity `objs`.

    Any strings included amongst `objs` are discarded, with a logged warning; these
    usually indicate that a quantity is referenced which is not in the Computer.
    """
    objs = tuple(filter_concat_args(objs))
    to_keep = dict(units=True) if len(set(collect_units(*objs))) == 1 else {}

    if isinstance(objs[0], AttrSeries):
        try:
            # Retrieve a "dim" keyword argument
            dim = kwargs.pop("dim")
        except KeyError:
            pass
        else:
            if isinstance(dim, pd.Index):
                # Convert a pd.Index argument to names and keys
                kwargs["names"] = [dim.name]
                kwargs["keys"] = dim.values
            else:
                # Something else; warn and discard
                log.warning(f"Ignore concat(…, dim={repr(dim)})")

        # Ensure objects have aligned dimensions
        _objs = [objs[0]]
        _objs.extend(
            map(lambda o: cast(AttrSeries, o).align_levels(_objs[0])[1], objs[1:])
        )

        result = pd.concat(_objs, **kwargs)
    else:
        # xr.merge() and xr.combine_by_coords() are not usable with sparse ≤ 0.14; they
        # give "IndexError: Only one-dimensional iterable indices supported." when the
        # objects have >1 dimension. Arbitrarily choose the first dimension of the first
        # of `objs` to concatenate along.
        # FIXME this may result in non-unique indices; avoid this.
        kwargs.setdefault("dim", (objs[0].dims or [None])[0])

        result = xr.concat(cast(xr.DataArray, objs), **kwargs)._sda.convert()

    return objs[0]._keep(result, name=True, **to_keep)


def convert_units(qty: "TQuantity", units: "UnitLike") -> "TQuantity":
    """Convert magnitude of `qty` from its current units to `units`.

    Parameters
    ----------
    units : str or pint.Unit
        Units to assign to `qty`.

    Raises
    ------
    ValueError
        if `units` does not match the dimensionality of the current units of `qty`.
    """
    registry, existing, existing_dims, new_units = _unit_args(qty, units)

    try:
        # NB use a factor because pint.Quantity cannot wrap AttrSeries
        factor = registry.Quantity(1.0, existing).to(new_units).magnitude
    except pint.DimensionalityError:
        raise ValueError(
            f"Existing dimensionality {existing_dims!r} cannot be converted to {units} "
            f"with dimensionality {new_units.dimensionality!r}"
        ) from None

    return qty._keep(qty * factor, name=True, attrs=True, units=new_units)


def disaggregate_shares(quantity: "TQuantity", shares: "TQuantity") -> "TQuantity":
    """Deprecated: Disaggregate `quantity` by `shares`.

    This operator is identical to :func:`mul`; use :func:`mul` and its helper instead.
    """
    return mul(quantity, shares)


@Operator.define(helper=add_binop)
def div(numerator: "TQuantity | float", denominator: "TQuantity") -> "TQuantity":
    """Compute the ratio `numerator` / `denominator`.

    Parameters
    ----------
    numerator : .Quantity
    denominator : .Quantity

    See also
    --------
    add_binop
    """
    return numerator / denominator


#: Alias of :func:`~genno.operator.div`, for backwards compatibility.
#:
#: .. note:: This may be deprecated and possibly removed in a future version.
ratio = div


def drop_vars(
    qty: "TQuantity",
    names: str | Iterable[Hashable] | Callable[["TQuantity"], str | Iterable[Hashable]],
    *,
    errors="raise",
) -> "TQuantity":
    """Return a Quantity with dropped variables (coordinates).

    Like :meth:`xarray.DataArray.drop_vars`.
    """
    return qty.drop_vars(names)


def expand_dims(
    qty: "TQuantity",
    dim: Hashable | Sequence[Hashable] | Mapping[Any, Any] | None = None,
    axis: int | Sequence[int] | None = None,
    create_index_for_new_dim: bool = True,
    **dim_kwargs: Any,
) -> "TQuantity":
    """Return a new object with (an) additional dimension(s).

    Like :meth:`xarray.DataArray.expand_dims`.
    """
    return qty.expand_dims(dim, axis, create_index_for_new_dim, **dim_kwargs)


def group_sum(qty: "TQuantity", group: str, sum: str) -> "TQuantity":
    """Group by dimension `group`, then sum across dimension `sum`.

    The result drops the latter dimension.
    """
    return concat(
        *[cast("TQuantity", values.sum(dim=[sum])) for _, values in qty.groupby(group)],
        dim=group,
    )


def index_to(
    qty: "TQuantity",
    dim_or_selector: str | Mapping,
    label: Hashable | None = None,
) -> "TQuantity":
    """Compute an index of `qty` against certain of its values.

    If the label is not provided, :func:`index_to` uses the label in the first position
    along the identified dimension.

    Parameters
    ----------
    qty : :class:`~genno.Quantity`
    dim_or_selector : str or mapping
        If a string, the ID of the dimension to index along.
        If a mapping, it must have only one element, mapping a dimension ID to a label.
    label : Hashable
        Label to select along the dimension, required if `dim_or_selector` is a string.
    Raises
    ------
    TypeError
        if `dim_or_selector` is a mapping with length != 1.
    """
    if isinstance(dim_or_selector, Mapping):
        if len(dim_or_selector) != 1:
            raise TypeError(
                f"Got {dim_or_selector}; expected a mapping from 1 key to 1 value"
            )
        dim, label = dict(dim_or_selector).popitem()
    else:
        # Unwrap dask.core.literals
        dim = getattr(dim_or_selector, "data", dim_or_selector)
        label = getattr(label, "data", label)

    if label is None:
        # Choose a label on which to normalize
        label = qty.coords[dim][0].item()
        log.info(f"Normalize quantity {qty.name} on {dim}={label}")

    return div(qty, qty.sel({dim: label}))


def interpolate(
    qty: "TQuantity",
    coords: Mapping[Hashable, Any] | None = None,
    method: "types.InterpOptions" = "linear",
    assume_sorted: bool = True,
    kwargs: Mapping[str, Any] | None = None,
    **coords_kwargs: Any,
) -> "TQuantity":
    """Interpolate `qty`.

    For the meaning of arguments, see :meth:`xarray.DataArray.interp`. When
    :data:`.CLASS` is :class:`.AttrSeries`, only 1-dimensional interpolation (one key
    in `coords`) is tested/supported.
    """
    if assume_sorted is not True:
        log.warning(f"interpolate(…, assume_sorted={assume_sorted}) ignored")

    return qty.interp(coords, method, assume_sorted, kwargs, **coords_kwargs)


@Operator.define()
def load_file(
    path: Path,
    dims: Collection[Hashable] | Mapping[Hashable, Hashable] = {},
    units: "UnitLike | None" = None,
    name: str | None = None,
) -> Any:
    """Read the file at `path` and return its contents as a :class:`~genno.Quantity`.

    Some file formats are automatically converted into objects for direct use in genno
    computations:

    :file:`.csv`:
       Converted to :class:`.Quantity`. CSV files must have a 'value' column; all others
       are treated as indices, except as given by `dims`. Lines beginning with '#' are
       ignored.

    User code **may** define an operator with the same name ("load_file") in order to
    override this behaviour and/or add tailored support for others data file formats,
    for instance specific kinds of :file:`.json`, :file:`.xml`, :file:`.yaml`,
    :file:`.ods`, :file:`.xlsx`, or other file types.

    Parameters
    ----------
    path : pathlib.Path
        Path to the file to read.
    dims : collections.abc.Collection or collections.abc.Mapping, optional
        If a collection of names, other columns besides these and 'value' are discarded.
        If a mapping, the keys are the column labels in `path`, and the values are the
        target dimension names.
    units : str or pint.Unit
        Units to apply to the loaded Quantity.
    name : str
        Name for the loaded Quantity.

    See also
    --------
    add_load_file
    """
    # TODO optionally cache: if the same Computer is used repeatedly, then the file will
    #      be read each time; instead cache the contents in memory.
    if path.suffix == ".csv":
        return _load_file_csv(path, dims, units, name)
    elif path.suffix in (".xls", ".xlsx", ".yaml"):  # pragma: no cover
        raise NotImplementedError  # To be handled by downstream code
    else:
        # Default
        return open(path).read()


@load_file.helper
def add_load_file(func, c: "genno.Computer", path, key=None, **kwargs):
    """:meth:`.Computer.add` helper for :func:`.load_file`.

    Add a task to load an exogenous quantity from `path`. Computing the `key` or using
    it in other computations causes `path` to be loaded and converted to
    :class:`.Quantity`.

    Parameters
    ----------
    path : os.PathLike
        Path to the file, e.g. '/path/to/foo.ext'.
    key : str or .Key, optional
        Key for the quantity read from the file.

    Other parameters
    ----------------
    dims : dict or list or set
        Either a collection of names for dimensions of the quantity, or a mapping from
        names appearing in the input to dimensions.
    units : str or pint.Unit
        Units to apply to the loaded Quantity.

    Returns
    -------
    .Key
        Either `key` (if given) or e.g. ``file foo.ext`` based on the `path` name,
        without directory components.
    """
    path = Path(path)
    key = key if key else "file {}".format(path.name)
    return c.add_single(key, partial(func, path, **kwargs), strict=True)


UNITS_RE = re.compile(r"# Units?: (.*)\s+")


def _load_file_csv(
    path: Path,
    dims: Collection[Hashable] | Mapping[Hashable, Hashable] = {},
    units: "UnitLike | None" = None,
    name: str | None = None,
) -> "AnyQuantity":
    # Peek at the header, if any, and match a units expression
    with open(path, "r", encoding="utf-8") as f:
        for line, match in map(lambda li: (li, UNITS_RE.fullmatch(li)), f):
            if match:
                if units:
                    log.warning(f"Replace {match.group(1)!r} from file with {units!r}")
                else:
                    units = match.group(1)
                break
            elif not line.startswith("#"):
                break  # Give up at first non-commented line

    # Read the data
    data = pd.read_csv(path, comment="#", skipinitialspace=True)

    # Index columns
    index_columns = data.columns.tolist()
    index_columns.remove("value")

    try:
        # Retrieve the unit column from the file
        units_col = data.pop("unit").unique()
        index_columns.remove("unit")
    except KeyError:
        pass  # No such column; use None or argument value
    else:
        # Use a unique value for units of the quantity
        if len(units_col) > 1:
            raise ValueError(
                f"Cannot load {path} with non-unique units {repr(units_col)}"
            )
        elif units and units not in units_col:
            raise ValueError(
                f"Explicit units {units} do not match {units_col[0]} in {path}"
            )
        units = units_col[0]

    if dims:
        # Convert a list, set, etc. to a dict
        dims = dims if isinstance(dims, Mapping) else {d: d for d in dims}

        # - Drop columns not mentioned in *dims*
        # - Rename columns according to *dims*
        data = data.drop(columns=list(set(index_columns) - set(dims.keys()))).rename(
            columns=dims
        )

        index_columns = list(data.columns)
        index_columns.pop(index_columns.index("value"))

    # Decode units and multiplier
    units, k = units_with_multiplier(units)

    # Prepare a quantity object
    return genno.Quantity(
        k * data.set_index(index_columns)["value"], units=units, name=name
    )


@Operator.define(helper=add_binop)
def mul(*quantities: "TQuantity") -> "TQuantity":
    """Compute the product of any number of `quantities`.

    See also
    --------
    add_binop
    """
    return reduce(operator.mul, quantities)


#: Alias of :func:`~genno.operator.mul`, for backwards compatibility.
#:
#: .. note:: This may be deprecated and possibly removed in a future version.
product = mul


def pow(a: "TQuantity", b: "TQuantity | int") -> "TQuantity":
    """Compute `a` raised to the power of `b`.

    Returns
    -------
    .Quantity
        If `b` is :class:`int` or a Quantity with all :class:`int` values that are equal
        to one another, then the quantity has the units of `a` raised to this power;
        for example, "kg²" → "kg⁴" if `b` is 2. In other cases, there are no meaningful
        units, so the returned quantity is dimensionless.
    """
    return a**b


def random_qty(shape: dict[str, int], **kwargs) -> "AnyQuantity":
    """Return a Quantity with `shape` and random contents.

    Parameters
    ----------
    shape : dict
        Mapping from dimension names (:class:`str`) to lengths along each dimension
        (:class:`int`).
    **kwargs
        Other keyword arguments to :class:`.Quantity`.

    Returns
    -------
    .Quantity
        Random data with one dimension for each key in `shape`, and coords along those
        dimensions like "foo1", "foo2", with total length matching the value from
        `shape`. If `shape` is empty, a scalar (0-dimensional) Quantity.
    """
    return genno.Quantity(
        np.random.rand(*shape.values()) if len(shape) else np.random.rand(1)[0],
        coords={
            dim: [f"{dim}{i}" for i in range(length)] for dim, length in shape.items()
        },
        **kwargs,
    )


def relabel(
    qty: "TQuantity",
    labels: Mapping[Hashable, Mapping] | None = None,
    **dim_labels: Mapping,
) -> "TQuantity":
    """Replace specific labels along dimensions of `qty`.

    Parameters
    ----------
    labels :
        Keys are strings identifying dimensions of `qty`; values are further mappings
        from original labels to new labels. Dimensions and labels not appearing in `qty`
        have no effect.
    dim_labels :
        Mappings given as keyword arguments, where argument name is the dimension.

    Raises
    ------
    ValueError
        if both `labels` and `dim_labels` are given.
    """
    # NB pandas uses the term "levels [of a MultiIndex]"; xarray uses "coords [for a
    # dimension]".
    # TODO accept callables as values in `mapper`, as DataArray.assign_coords() does
    maps = either_dict_or_kwargs(labels, dim_labels, "relabel")

    # Iterate over (dim, label_map) for only dims included in `qty`
    iter = filter(lambda kv: kv[0] in qty.dims, maps.items())

    def map_labels(mapper, values):
        """Generate the new labels for a single dimension."""
        return list(map(lambda label: mapper.get(label, label), values))

    if isinstance(qty, AttrSeries):
        # Prepare a new index
        idx = qty.index.copy()
        for dim, label_map in iter:
            # - Look up numerical index of the dimension in `idx`
            # - Retrieve the existing levels.
            # - Map to new levels.
            # - Assign, creating a new index
            idx = idx.set_levels(
                map_labels(label_map, idx.levels[idx.names.index(dim)]), level=dim
            )

        # Assign the new index to a copy of qty
        return qty.set_axis(idx)
    else:
        return cast(SparseDataArray, qty).assign_coords(
            {dim: map_labels(m, qty.coords[dim].data) for dim, m in iter}
        )


def rename(
    qty: "TQuantity",
    new_name_or_name_dict: Hashable | Mapping[Any, Hashable] = None,
    **names: Hashable,
) -> "TQuantity":
    """Returns a new Quantity with renamed dimensions or a new name.

    Like :meth:`.xarray.DataArray.rename`, and identical in behaviour to
    :func:`.rename_dims`.
    """
    return qty.rename(new_name_or_name_dict, **names)


def rename_dims(
    qty: "TQuantity",
    name_dict: Hashable | Mapping[Any, Hashable] = None,
    **names: Hashable,
) -> "TQuantity":
    """Returns a new Quantity with renamed dimensions or a new name.

    Like :meth:`.xarray.DataArray.rename`, and identical in behaviour to
    :func:`.rename`. The two names are provided for more expressive user code.
    """
    return qty.rename(name_dict, **names)


def round(qty: "TQuantity", *args, **kwargs) -> "TQuantity":
    """Like :meth:`xarray.DataArray.round`."""
    return qty.round(*args, **kwargs)


def select(
    qty: "TQuantity",
    indexers: Mapping[Hashable, Iterable[Hashable]],
    *,
    inverse: bool = False,
    drop: bool = False,
) -> "TQuantity":
    """Select from `qty` based on `indexers`.

    Parameters
    ----------
    indexers : dict
        Elements to be selected from `qty`. Mapping from dimension names (:class:`str`)
        to either:

        - :class:`list` of `str`: coords along the respective dimension of `qty`, or
        - :class:`xarray.DataArray`: xarray-style indexers.

        Values not appearing in the dimension coords are silently ignored.
    inverse : bool, optional
        If :obj:`True`, *remove* the items in indexers instead of keeping them.
    drop : bool, optional
        If :obj:`True`, drop dimensions that are indexed by a scalar value (for
        instance, :py:`"foo"` or :py:`999`) in `indexers`. Note that dimensions indexed
        by a length-1 list of labels (for instance :py:`["foo"]`) are not dropped; this
        behaviour is consistent with :class:`xarray.DataArray`.
    """
    # Identify the type of the first value in `indexers`
    _t = type(next(chain(iter(indexers.values()), [None])))

    if _t is xr.DataArray:
        if inverse:
            raise NotImplementedError("select(…, inverse=True) with DataArray indexers")

        # Pass through
        idx = indexers
    else:
        # Predicate for containment
        op2 = operator.not_ if inverse else operator.truth

        coords = qty.coords
        idx = dict()
        for dim, labels in indexers.items():
            if is_scalar(labels):
                # Check coords equal to scalar label
                op1 = partial(operator.eq, labels)
                # Take 1 item
                item: int | slice = 0
            else:
                # Check coords contained in collection of labels; take all
                op1, item = partial(operator.contains, set(labels)), slice(None)

            try:
                # Use only the values from `indexers` (not) appearing in `qty.coords`
                idx[dim] = list(filter(lambda x: op2(op1(x)), coords[dim].data))[item]
            except IndexError:
                raise KeyError(f"value {labels!r} not found in index {dim!r}")

    return qty.sel(idx, drop=drop)


@Operator.define(helper=add_binop)
def sub(a: "TQuantity", b: "TQuantity") -> "TQuantity":
    """Subtract `b` from `a`.

    See also
    --------
    add_binop
    """
    return add(a, -b)


@Operator.define()
def sum(
    quantity: "TQuantity",
    weights: "TQuantity | None" = None,
    dimensions: list[str] | None = None,
) -> "TQuantity":
    """Sum `quantity` over `dimensions`, with optional `weights`.

    Parameters
    ----------
    weights : .Quantity, optional
        If `dimensions` is given, `weights` must have at least these dimensions.
        Otherwise, any dimensions are valid.
    dimensions : list of str, optional
        If not provided, sum over all dimensions. If provided, sum over these
        dimensions.
    """
    if weights is None:
        _w: "TQuantity" = genno.Quantity(1.0)
        w_total: "TQuantity" = genno.Quantity(1.0)
    else:
        _w, w_total = weights, weights.sum(dim=dimensions)
        if w_total.shape == ():
            w_total = w_total.item()

    return quantity._keep((quantity * _w).sum(dim=dimensions) / w_total, name=True)


@sum.helper
def add_sum(
    func, c: "genno.Computer", key, qty, weights=None, dimensions=None, **kwargs
) -> KeyLike | tuple[KeyLike, ...]:
    """:meth:`.Computer.add` helper for :func:`.sum`.

    If `key` has the name "*", the returned key has name and dimensions inferred from
    `qty` and `dimensions`, and only the tag (if any) of `key` is preserved.

    Parameters
    ----------
    """
    key = Key(key)
    if key.name == "*":
        q = Key(qty)
        key = (q.drop(*dimensions) if dimensions else q.drop_all()).add_tag(key.tag)

    return c.add(key, func, qty, weights=weights, dimensions=dimensions, **kwargs)


def unique_units_from_dim(
    qty: "TQuantity", dim: str, *, fail: str | int = "raise"
) -> "TQuantity":
    """Assign :attr:`.Quantity.units` using coords from the dimension `dim`.

    The dimension `dim` is dropped from the result.

    Raises
    ------
    ValueError
        if (a) `fail` is "raise" (the default) and (b) the dimension `dim` contains more
        than one unique value. If `fail` is anything else, a message is logged with
        level `fail`, and the returned Quantity is dimensionless.
    """
    if not qty.size:
        return qty

    units = qty.coords[dim].data
    if len(units) == 1:
        sel = {dim: units[0]}
        assign = units[0]
    else:
        msg = (
            f"Non-unique units {sorted(map(str, units))!r} for {type(qty).__name__} "
            + repr(qty.name)
        )
        if fail == "raise":
            raise ValueError(msg)
        else:
            log.log(
                fail if isinstance(fail, int) else getattr(logging, fail.upper()),
                f"{msg}; discard",
            )
            sel = {}
            assign = "dimensionless"

    return qty.sel(sel, drop=True).pipe(assign_units, assign)


def where(
    qty: "TQuantity", cond: Any, other: Any = dtypes.NA, drop: bool = False
) -> "TQuantity":
    """Call :meth:`.Quantity.where`."""
    return qty.where(cond, other, drop)


def wildcard_qty(value, units, dims: Sequence[Hashable]) -> "AnyQuantity":
    """Return a Quantity with 1 label "*" along each of `dims`."""
    if genno.Quantity is SparseDataArray:
        # Convert `value` into a list-of-lists of appropriate depth
        value = reduce(lambda x, y: [x], range(len(dims)), value)
    return genno.Quantity(value, coords={d: ["*"] for d in dims}, units=units)


def _format_header_comment(kwargs) -> str:
    value = kwargs.pop("header_comment", "")

    if kwargs.pop("header_datetime", False):
        tz = datetime.now().astimezone().tzinfo
        value += os.linesep + f"Generated: {datetime.now(tz).isoformat()}" + os.linesep

    units = kwargs.pop("units", "")
    if kwargs.pop("header_units", False):
        value += os.linesep + f"Units: {units}" + os.linesep

    if not len(value):
        return value

    from textwrap import indent

    return indent(value + os.linesep, "# ", lambda line: True)


@singledispatch
def write_report(
    quantity: object, path: str | PathLike, kwargs: dict | None = None
) -> None:
    """Write a quantity to a file.

    :py:`write_report()` is a :func:`~functools.singledispatch` function. This means
    that user code can extend this operator to support different types for the
    `quantity` argument:

    .. code-block:: python

       import genno.operator

       @genno.operator.write_report.register
       def my_writer(qty: MyClass, path, kwargs):
           ... # Code to write MyClass to file

    Parameters
    ----------
    quantity :
        Object to be written. The base implementation supports :class:`.Quantity` and
        :class:`pandas.DataFrame`.
    path : str or pathlib.Path
        Path to the file to be written.
    kwargs :
        Keyword arguments. For the base implementation, these are passed to
        :meth:`pandas.DataFrame.to_csv` or :meth:`pandas.DataFrame.to_excel` (according
        to `path`), except for:

        - "header_comment": handled only for `path` ending in :file:`.csv`. Multi-line
          text that is prepended to the file, with comment characters ("# ") before
          each line.
        - "header_datetime": handled only for :file:`.csv`. If :any:`True` (default:
          :any:`False`), append a line like "Generated: 2025-02-20T…" after the
          `header_comment`.
        - "header_units": handled only for :file:.csv`. If :any:`True` (default:
          :any:`False`), append a line like "Units: kg / m / s**2" after the
          `header_comment`.
        - "units": used with "header_units", above. If `quantity` is |Quantity|, this
          is retrieved automatically from its units attribute; if
          :class:`pandas.DataFrame`, it must be provided explicitly.

    Raises
    ------
    NotImplementedError
        If `quantity` is of a type not supported by the base implementation or any
        overloads.
    """
    raise NotImplementedError(f"Write {type(quantity)} to file")


@write_report.register
def _(quantity: str, path: str | PathLike, kwargs: dict | None = None):
    Path(path).write_text(quantity)


@write_report.register
def _(quantity: pd.DataFrame, path: str | PathLike, kwargs: dict | None = None) -> None:
    path = Path(path)

    kwargs = kwargs or dict()
    kwargs.setdefault("index", False)

    # Format header comment even if it is not to be used; this consumes the related
    # keyword arguments so they are not passed to DataFrame.to_{csv,excel}().
    header = _format_header_comment(kwargs)

    if path.suffix == ".csv":
        with open(path, "wb") as f:
            f.write(header.encode())
            quantity.to_csv(f, **kwargs)
    elif path.suffix == ".xlsx":
        kwargs.setdefault("merge_cells", False)
        quantity.to_excel(path, **kwargs)
    else:
        raise NotImplementedError(f"Write pandas.DataFrame to {path.suffix!r}")


@write_report.register(AttrSeries)
@write_report.register(SparseDataArray)
def _(
    quantity: "AnyQuantity",  # register() only handles bare AnyQuantity in Python ≥3.11
    path: str | PathLike,
    kwargs: dict | None = None,
) -> None:
    # Convert the Quantity to a pandas.DataFrame, then write
    kwargs = deepcopy(kwargs or dict())
    kwargs.setdefault("units", f"{quantity.units:~}")
    write_report(quantity.to_dataframe().reset_index(), path, kwargs)
