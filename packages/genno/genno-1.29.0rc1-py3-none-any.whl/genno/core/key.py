import logging
import re
from collections.abc import Callable, Generator, Hashable, Iterable, Iterator, Sequence
from functools import partial, singledispatch
from itertools import chain, compress
from types import MappingProxyType
from typing import TYPE_CHECKING, SupportsInt
from warnings import warn

from .attrseries import AttrSeries
from .sparsedataarray import SparseDataArray

if TYPE_CHECKING:
    from .quantity import AnyQuantity


log = logging.getLogger(__name__)

#: Regular expression for valid key strings.
EXPR = re.compile(r"^(?P<name>[^:]+)(:(?P<dims>([^:-]*-)*[^:-]+)?(:(?P<tag>[^:]*))?)?$")

#: Regular expression for non-keylike strings.
BARE_STR = re.compile(r"^\s*(?P<name>[^:]+)\s*$")


@singledispatch
def _name_dims_tag(value) -> tuple[str, tuple[str, ...], str | None]:
    """Convert various `value`s into (name, dims, tag) tuples.

    Helper for :meth:`.Key.__init__`.
    """
    raise TypeError(type(value))


@_name_dims_tag.register
def _(value: str):
    """Parse a string that may contain a Key expression."""
    match = EXPR.match(value)
    if match is None:
        raise ValueError(f"Invalid key expression: {repr(value)}")
    groups = match.groupdict()
    return (
        groups["name"],
        tuple() if not groups["dims"] else tuple(groups["dims"].split("-")),
        groups["tag"],
    )


@_name_dims_tag.register(AttrSeries)
@_name_dims_tag.register(SparseDataArray)
def _(value: "AnyQuantity"):  # register() only handles bare AnyQuantity in Python ≥3.11
    """Return (name, dims, tag) that describe an existing Quantity."""
    return str(value.name), tuple(map(str, value.dims)), None


class KeyGeneratorMixIn:
    """Mix-in class for classes that can derive :class:`.Key` from a base."""

    __slots__ = ("_base", "_generated")

    _base: "Key"
    _generated: list[Hashable]

    def __init__(self) -> None:
        self._generated = []

    def __call__(self, value: Hashable | None = None) -> "Key":
        return next(self) if value is None else self[value]

    def __getitem__(self, value: Hashable) -> "Key":
        value = int(value) if isinstance(value, SupportsInt) else str(value)
        if value not in self._generated:
            self._generated.append(value)
        return self._base.add_tag(str(value))

    def __next__(self) -> "Key":
        return self[self._next_int_tag()]

    def _next_int_tag(self) -> int:
        return max([-1] + [t for t in self._generated if isinstance(t, int)]) + 1

    @property
    def generated(self) -> tuple["Key", ...]:
        """Sequence of previously-created :class:`Keys <.Key>`."""
        return tuple(self._base.add_tag(str(k)) for k in self._generated)

    @property
    def last(self) -> "Key":
        """The most recently created :class:`.Key`."""
        return self._base.add_tag(str(self._generated[-1]))


class Key(KeyGeneratorMixIn):
    """A hashable key for a quantity that includes its dimensionality."""

    __slots__ = ("_dims", "_hash", "_name", "_str", "_tag")

    _dims: tuple[str, ...]
    _hash: int
    _name: str
    _str: str
    _tag: str | None

    def __init__(
        self,
        name_or_value: "str | Key | AnyQuantity",
        dims: Iterable[str] = [],
        tag: str | None = None,
        _fast: bool = False,
    ):
        if _fast:
            # Fast path: don't handle arguments
            assert isinstance(name_or_value, str)
            self._name = name_or_value
            self._dims = tuple(dims)
            self._tag = tag or None
        else:
            # Convert various values into a (name, dims, tags)
            self._name, _dims, _tag = _name_dims_tag(name_or_value)

            # Check for conflicts between dims inferred from name_or_value and any
            # direct argument
            # TODO handle resolveable combinations without raising exceptions
            if bool(_dims) and bool(dims):
                raise ValueError(
                    f"Conflict: {dims = } argument vs. {_dims!r} from {name_or_value!r}"
                )
            elif bool(_tag) and bool(tag):
                raise ValueError(
                    f"Conflict: {tag = } argument vs. {_tag!r} from {name_or_value!r}"
                )

            self._dims = _dims or tuple(dims)
            self._tag = _tag or tag

        super().__init__()
        self._base = self

        # Pre-compute string representation and hash
        self._str = (
            self._name
            + ":"
            + "-".join(self._dims)
            + (f":{self._tag}" if self._tag else "")
        )
        # Hash is independent of dim order
        self._hash = hash(
            self._name
            + ":"
            + "-".join(sorted(self._dims))
            + (f":{self._tag}" if self._tag else "")
        )

    # Class methods

    @classmethod
    def bare_name(cls, value) -> str | None:
        """If `value` is a bare name (no dims or tags), return it; else :obj:`None`."""
        if not isinstance(value, str):
            return None
        match = BARE_STR.match(value)
        return match.group("name") if match else None

    @classmethod
    def from_str_or_key(
        cls,
        value: "str | Key | AnyQuantity",
        drop: Iterable[str] | bool = [],
        append: Iterable[str] = [],
        tag: str | None = None,
    ) -> "Key":
        """Return a new Key from *value*.

        .. versionchanged:: 1.18.0

           Calling :meth:`from_str_or_key` with a single argument is no longer
           necessary; simply give the same `value` as an argument to :class:`Key`.

           The class method is retained for convenience when calling with multiple
           arguments. However, the following are equivalent and may be more readable:

           .. code-block:: python

              k1 = Key("foo:a-b-c:t1", drop="b", append="d", tag="t2")
              k2 = Key("foo:a-b-c:t1").drop("b").append("d)"

        Parameters
        ----------
        value : str or .Key
            Value to use to generate a new Key.
        drop : list of str or :obj:`True`, optional
            Existing dimensions of *value* to drop. See :meth:`drop`.
        append : list of str, optional
            New dimensions to append to the returned Key. See :meth:`append`.
        tag : str, optional
            Tag for returned Key. If *value* has a tag, the two are joined
            using a '+' character. See :meth:`add_tag`.

        Returns
        -------
        :class:`Key`
        """
        base = cls(value)

        # Return quickly if no further manipulations are required
        if not any([drop, append, tag]):
            warn(
                "Calling Key.from_str_or_key(value) with no other arguments is no "
                "longer necessary; simply use Key(value)",
                FutureWarning,
                stacklevel=2,
            )
            return base

        # mypy is fussy here
        drop_args: tuple[str | bool, ...] = tuple(
            [drop] if isinstance(drop, bool) else drop
        )

        # Drop and append dimensions; add tag
        return base.drop(*drop_args).append(*tuple(append)).add_tag(tag)

    @classmethod
    def product(cls, new_name: str, *keys, tag: str | None = None) -> "Key":
        """Return a new Key that has the union of dimensions on *keys*.

        Dimensions are ordered by their first appearance:

        1. First, the dimensions of the first of the *keys*.
        2. Next, any additional dimensions in the second of the *keys* that
           were not already added in step 1.
        3. etc.

        Parameters
        ----------
        new_name : str
            Name for the new Key. The names of *keys* are discarded.
        keys
            May include instances of :class:`.Key`, :class:`str` (converted to Key), or
            :class:`Quantity` (the dimensions of the quantity are used directly).
        """
        # Iterable of dimension names from all keys, in order, with repetitions
        dims = chain(
            *map(
                lambda k: cls(k).dims
                if isinstance(k, (AttrSeries, SparseDataArray, Key, str))
                else (),
                keys,
            )
        )

        # Return new key. Use dict to keep only unique *dims*, in same order
        return cls(new_name, dict.fromkeys(dims).keys()).add_tag(tag)

    def __add__(self, other: str) -> "Key":
        if not isinstance(other, str):
            raise TypeError(type(other))
        return self.add_tag(other)

    def __sub__(self, other: str | Iterable[str]) -> "Key":
        return self.remove_tag(*((other,) if isinstance(other, str) else other))

    def __mul__(self, other: "str | Key | Sequence[str]") -> "Key":
        if isinstance(other, str):
            other_dims: Sequence[str] = (other,)
        elif isinstance(other, Key):
            other_dims = other.dims
        elif isinstance(other, Sequence):
            other_dims = other
        else:
            raise TypeError(type(other))

        return self.append(*other_dims)

    def __truediv__(self, other: "str | Key | Sequence[str]") -> "Key":
        if isinstance(other, str):
            other_dims: Sequence[str] = (other,)
        elif isinstance(other, Key):
            other_dims = other.dims
        elif isinstance(other, Sequence):
            other_dims = other
        else:
            raise TypeError(type(other))

        return self.drop(*other_dims)

    def __repr__(self) -> str:
        """Representation of the Key, e.g. '<name:dim1-dim2-dim3:tag>."""
        return f"<{self._str}>"

    def __str__(self) -> str:
        """String equivalent of the Key, e.g. 'name:dim1-dim2-dim3:tag'."""
        return self._str  # Return the pre-computed value

    def __hash__(self):
        """Key hashes the same as :py:`str(Key)`."""
        return self._hash

    def __eq__(self, other) -> bool:
        """Key is equal to :py:`str(Key)`."""
        try:
            other = Key(other)
        except TypeError:
            return NotImplemented

        return (
            (self.name == other.name)
            and (set(self.dims) == set(other.dims))
            and (self.tag == other.tag)
        )

    # Less-than and greater-than operations, for sorting
    def __lt__(self, other) -> bool:
        if isinstance(other, Key):
            return str(self.sorted) < str(other.sorted)
        elif isinstance(other, str):
            return str(self.sorted) < other
        else:
            return NotImplemented

    def __gt__(self, other) -> bool:
        if isinstance(other, Key):
            return str(self.sorted) > str(other.sorted)
        elif isinstance(other, str):
            return str(self.sorted) > other
        else:
            return NotImplemented

    @property
    def name(self) -> str:
        """Name of the quantity, :class:`str`."""
        return self._name

    @property
    def dims(self) -> tuple[str, ...]:
        """Dimensions of the quantity, :class:`tuple` of :class:`str`."""
        return self._dims

    @property
    def tag(self) -> str | None:
        """Quantity tag, :class:`str` or :obj:`None`."""
        return self._tag

    @property
    def sorted(self) -> "Key":
        """A version of the Key with its :attr:`.dims` :func:`sorted`."""
        return Key(self._name, sorted(self._dims), self._tag, _fast=True)

    def rename(self, name: str) -> "Key":
        """Return a Key with a replaced `name`."""
        return Key(name, self._dims, self._tag, _fast=True)

    def drop(self, *dims: str | bool) -> "Key":
        """Return a new Key with `dims` dropped."""
        return Key(
            self._name,
            tuple() if dims == (True,) else filter(lambda d: d not in dims, self._dims),
            self._tag,
            _fast=True,
        )

    def drop_all(self) -> "Key":
        """Return a new Key with all dimensions dropped / zero dimensions."""
        return Key(self._name, tuple(), self._tag, _fast=True)

    def append(self, *dims: str) -> "Key":
        """Return a new Key with additional dimensions `dims`."""
        return Key(self._name, list(self._dims) + list(dims), self._tag, _fast=True)

    def add_tag(self, tag: str | None) -> "Key":
        """Return a new Key with `tag` appended."""
        return Key(
            self._name, self._dims, "+".join(filter(None, [self._tag, tag])), _fast=True
        )

    def iter_sums(self) -> Generator[tuple["Key", Callable, "Key"], None, None]:
        """Generate (key, task) for all possible partial sums of the Key."""
        from genno.operator import sum

        for agg_dims, others in combo_partition(self.dims):
            yield (
                Key(self._name, agg_dims, self.tag, _fast=True),
                partial(sum, dimensions=others, weights=None),
                self,
            )

    def remove_tag(self, *tags: str) -> "Key":
        """Return a key with any of `tags` dropped.

        Raises
        ------
        ValueError
            If none of `tags` are in :attr:`.tags`.
        """
        new_tags = tuple(filter(lambda t: t not in tags, (self.tag or "").split("+")))
        new_tag = "+".join(new_tags) if new_tags else None
        if new_tag == self.tag:
            raise ValueError(f"No existing tags {tags!r} to remove")
        return Key(self._name, self._dims, new_tag, _fast=True)


@_name_dims_tag.register
def _(value: Key):
    """Return the (name, dims, tag) of an existing Key."""
    return value._name, value._dims, value._tag


class Keys:
    """A collection of :class:`.Key`.

    This is essentially the same as :class:`.types.SimpleNamespace`, except every
    attribute is a :class:`.Key`.
    """

    __slots__ = ("_keys",)

    _keys: dict[str, Key]

    def __init__(self, **kwargs: "KeyLike") -> None:
        object.__setattr__(self, "_keys", {})
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __delattr__(self, name: str) -> None:
        self._keys.pop(name)

    def __getattr__(self, name: str) -> "Key":
        try:
            return self._keys[name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self) -> str:
        return f"<{len(self._keys)} keys: {' '.join(sorted(self._keys))}>"

    def __setattr__(self, name: str, value: "Key") -> None:
        self._keys[name] = value if isinstance(value, Key) else Key(value)


class KeySeq(KeyGeneratorMixIn):
    """Utility class for generating similar :class:`Keys <.Key>`."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._base = Key(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<KeySeq from '{self._base!s}'>"

    # Particular to KeySeq

    @property
    def keys(self) -> MappingProxyType:
        """Read-only view of previously-created :class:`Keys <.Key>`.

        In the form of a :class:`dict` mapping tags (:class:`int` or :class:`str`) to
        :class:`.Key` values.
        """
        return MappingProxyType(
            {k: self._base.add_tag(str(k)) for k in self._generated}
        )

    @property
    def prev(self) -> Key:
        """Alias of :attr:`.KeyGeneratorMixin.last`."""
        return self.last

    # Access to Key properties
    @property
    def base(self) -> Key:
        """The base Key."""
        return self._base

    @property
    def name(self) -> str:
        """Name of the :attr:`.base` Key."""
        return self._base.name

    @property
    def dims(self) -> tuple[str, ...]:
        """Dimensions of the :attr:`.base` Key."""
        return self._base.dims

    @property
    def tag(self) -> str | None:
        """Tag of the :attr:`.base` Key."""
        return self._base.tag

    def __add__(self, other: str) -> "KeySeq":
        return KeySeq(self._base.__add__(other))

    def __mul__(self, other) -> "KeySeq":
        return KeySeq(self._base.__mul__(other))

    def __sub__(self, other: str | Iterable[str]) -> "KeySeq":
        return KeySeq(self._base.__sub__(other))

    def __truediv__(self, other) -> "KeySeq":
        return KeySeq(self._base.__truediv__(other))


#: Type shorthand for :class:`Key` or any other value that can be used as a key.
KeyLike = Key | str


def combo_partition(iterable):
    """Yield pairs of lists with all possible subsets of *iterable*."""
    # Format string for binary conversion, e.g. '04b'
    fmt = "0{}b".format(len(iterable))
    for n in range(2 ** len(iterable) - 1):
        # Two binary lists
        a, b = zip(*[(v, not v) for v in map(int, format(n, fmt))])
        yield list(compress(iterable, a)), list(compress(iterable, b))


def iter_keys(value: KeyLike | tuple[KeyLike, ...]) -> Iterator[Key]:
    """Yield :class:`Keys <Key>` from `value`.

    Raises
    ------
    TypeError
        `value` is not an iterable of :class:`Key`.

    See also
    --------
    .Computer.add
    """
    if isinstance(value, (Key, str)):
        yield Key(value)
        tmp: Iterator[KeyLike] = iter(())
    else:
        tmp = iter(value)
    for element in tmp:
        if not isinstance(element, Key):
            raise TypeError(type(element))
        yield element


def single_key(value: KeyLike | tuple[KeyLike, ...] | Iterator) -> Key:
    """Ensure `value` is a single :class:`Key`.

    Raises
    ------
    TypeError
        `value` is not a :class:`Key` or 1-tuple of :class:`Key`.

    See also
    --------
    .Computer.add
    """
    if isinstance(value, (Key, str)):
        return Key(value)

    tmp = iter(value)
    try:
        result = next(tmp)
    except StopIteration:
        raise TypeError("Empty iterable")
    else:
        try:
            next(tmp)
        except StopIteration:
            pass
        else:
            raise TypeError("Iterable of length >1")

    if isinstance(result, Key):
        return result
    else:
        raise TypeError(type(result))
