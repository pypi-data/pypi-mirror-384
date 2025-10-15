"""Compatibility with :mod:`xarray`."""

from abc import abstractmethod
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import numpy as np
import pandas as pd
import xarray
from xarray.core import dtypes
from xarray.core.coordinates import Coordinates
from xarray.core.indexes import Indexes
from xarray.core.utils import either_dict_or_kwargs, is_scalar

if TYPE_CHECKING:
    import xarray.core.types
    from xarray.core.types import Dims

T = TypeVar("T", covariant=True)

__all__ = [
    "Coordinates",
    "DataArrayLike",
    "Indexes",
    "dtypes",
    "either_dict_or_kwargs",
    "is_scalar",
]


class DataArrayLike(Protocol):
    """Protocol for a :class:`.xarray.DataArray` -like API.

    This class is used to set signatures and types for methods and attributes on
    :class:`.AttrSeries` class, which then supplies implementations of each method.
    Objects typed :class:`.AnyQuantity` see either the signatures of this protocol, or
    identical signatures for the same methods on :class:`~xarray.DataArray` via
    :class:`.SparseDataArray`.
    """

    # Type hints for mypy in downstream applications
    @abstractmethod
    def __len__(self) -> int: ...

    def __mod__(self, other): ...
    def __mul__(self, other): ...
    def __neg__(self): ...
    def __pow__(self, other): ...
    def __radd__(self, other): ...
    def __rmul__(self, other): ...
    def __rsub__(self, other): ...
    def __rtruediv__(self, other): ...
    def __truediv__(self, other): ...

    @property
    @abstractmethod
    def data(self) -> Any: ...

    @property
    @abstractmethod
    def coords(self) -> xarray.core.coordinates.DataArrayCoordinates: ...

    @property
    @abstractmethod
    def dims(self) -> tuple[Hashable, ...]: ...

    @property
    @abstractmethod
    def shape(self) -> tuple[int, ...]: ...

    @property
    @abstractmethod
    def size(self) -> int: ...

    def assign_coords(
        self,
        coords: Mapping[Any, Any] | None = None,
        **coords_kwargs: Any,
    ): ...

    @abstractmethod
    def astype(
        self,
        dtype,
        *,
        order=None,
        casting=None,
        subok=None,
        copy=None,
        keep_attrs=True,
    ): ...

    @abstractmethod
    def bfill(
        self,
        dim: Hashable,
        limit: int | None = None,
    ): ...

    @abstractmethod
    def clip(
        self,
        min: "xarray.core.types.ScalarOrArray | None" = None,
        max: "xarray.core.types.ScalarOrArray | None" = None,
        *,
        keep_attrs: bool | None = None,
    ): ...

    @abstractmethod
    def copy(
        self,
        deep: bool = True,
        data: Any = None,
    ): ...

    @abstractmethod
    def cumprod(
        self,
        dim: "Dims" = None,
        *,
        skipna: bool | None = None,
        keep_attrs: bool | None = None,
        **kwargs: Any,
    ): ...

    @abstractmethod
    def drop_vars(
        self,
        names: str | Iterable[Hashable] | Callable[[Any], str | Iterable[Hashable]],
        *,
        errors="raise",
    ): ...

    @abstractmethod
    def expand_dims(
        self,
        dim=None,
        axis=None,
        **dim_kwargs: Any,
    ): ...

    @abstractmethod
    def ffill(
        self,
        dim: Hashable,
        limit: int | None = None,
    ): ...

    @abstractmethod
    def groupby(
        self,
        group,
        squeeze: bool = True,
        restore_coord_dims: bool = False,
    ): ...

    @abstractmethod
    def interp(
        self,
        coords: Mapping[Any, Any] | None = None,
        method: "xarray.core.types.InterpOptions" = "linear",
        assume_sorted: bool = False,
        kwargs: Mapping[str, Any] | None = None,
        **coords_kwargs: Any,
    ): ...

    @abstractmethod
    def item(self, *args): ...

    @abstractmethod
    def max(
        self,
        dim: "Dims" = None,
        *,
        skipna: bool | None = None,
        keep_attrs: bool | None = None,
        **kwargs: Any,
    ): ...

    @abstractmethod
    def min(
        self,
        dim: "Dims" = None,
        *,
        skipna: bool | None = None,
        keep_attrs: bool | None = None,
        **kwargs: Any,
    ): ...

    @abstractmethod
    def pipe(
        self,
        func: Callable[..., T] | tuple[Callable[..., T], str],
        *args: Any,
        **kwargs: Any,
    ): ...

    @abstractmethod
    def rename(
        self,
        new_name_or_name_dict: Hashable | Mapping[Any, Hashable] = None,
        **names: Hashable,
    ): ...

    @abstractmethod
    def round(self, *args, **kwargs): ...

    @abstractmethod
    def sel(
        self,
        indexers: Mapping[Any, Any] | None = None,
        method: str | None = None,
        tolerance=None,
        drop: bool = False,
        **indexers_kwargs: Any,
    ): ...

    @abstractmethod
    def shift(
        self,
        shifts: Mapping[Any, int] | None = None,
        fill_value: Any = None,
        **shifts_kwargs: int,
    ): ...

    def squeeze(
        self,
        dim: Hashable | Iterable[Hashable] | None = None,
        drop: bool = False,
        axis: int | Iterable[int] | None = None,
    ): ...

    @abstractmethod
    def sum(
        self,
        dim: "Dims" = None,
        # Signature from xarray.DataArray
        *,
        skipna: bool | None = None,
        min_count: int | None = None,
        keep_attrs: bool | None = None,
        **kwargs: Any,
    ): ...

    @abstractmethod
    def to_dataframe(
        self,
        name: Hashable | None = None,
        dim_order: Sequence[Hashable] | None = None,
    ) -> pd.DataFrame: ...

    @abstractmethod
    def to_numpy(self) -> np.ndarray: ...

    @abstractmethod
    def where(self, cond: Any, other: Any = dtypes.NA, drop: bool = False): ...

    # Provided only for type-checking in other packages. AttrSeries implements;
    # SparseDataArray uses the xr.DataArray method.
    @abstractmethod
    def to_series(self) -> pd.Series: ...
