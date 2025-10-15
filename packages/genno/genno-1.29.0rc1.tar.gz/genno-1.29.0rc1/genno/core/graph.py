from collections.abc import Generator, Iterable, Sequence
from itertools import chain, tee
from operator import itemgetter
from typing import TYPE_CHECKING, Any

from .key import Key

if TYPE_CHECKING:
    from .key import KeyLike


def _key_arg(key: "KeyLike") -> str | Key:
    return Key.bare_name(key) or Key(key)


class Graph(dict):
    """A dictionary for a graph indexed by :class:`.Key`.

    Graph maintains indexes on set/delete/pop/update operations that allow for fast
    lookups/member checks in certain special cases:

    .. autosummary::

       unsorted_key
       full_key

    These basic features are used to provide higher-level helpers for
    :class:`.Computer`:

    .. autosummary::

       infer
    """

    _unsorted: dict["KeyLike", "KeyLike"] = dict()
    _full: dict[Key, Key] = dict()

    def __init__(self, *args, **kwargs) -> None:
        # Initialize members
        super().__init__(*args, **kwargs)

        # Initialize indices
        self._unsorted = dict()
        self._full = dict()

        # Index new keys
        for k in kwargs.keys():
            self._index(k)

    def _index(self, key: "KeyLike") -> None:
        """Add `key` to the indices."""
        k = _key_arg(key)
        if isinstance(k, Key):
            self._unsorted[k.sorted] = k
            nodim = k.drop(True)
            if len(k.dims) >= len(self._full.get(nodim, nodim).dims):
                self._full[nodim] = k
        else:
            self._unsorted[k] = key

    def _deindex(self, key: "KeyLike") -> None:
        """Remove `key` from the indices."""
        k = _key_arg(key)
        if isinstance(k, Key):
            self._unsorted.pop(k.sorted, None)
            self._full.pop(k.drop(True), None)
        else:
            self._unsorted.pop(k, None)

    def __contains__(self, item) -> bool:
        """:obj:`True` if `item` *or* a key with the same dims in a different order."""
        try:
            return super().__contains__(item) or bool(self.unsorted_key(item))
        except Exception:  # for instance, TypeError
            return False

    def __delitem__(self, key: "KeyLike") -> None:
        super().__delitem__(key)
        self._deindex(key)

    def __getitem__(self, key: "KeyLike"):
        return super().__getitem__(_key_arg(key))

    def __setitem__(self, key: "KeyLike", value: Any) -> None:
        super().__setitem__(key, value)
        self._index(key)

    def pop(self, *args):
        """Overload :meth:`dict.pop` to also call :meth:`_deindex`."""
        try:
            return super().pop(*args)
        finally:
            self._deindex(args[0])

    def update(self, arg=None, **kwargs):
        """Overload :meth:`dict.update` to also call :meth:`_index`."""
        if isinstance(arg, (Sequence, Generator)):
            arg0, arg1 = tee(arg)
            arg_keys = map(itemgetter(0), arg0)
        else:
            arg1 = arg or dict()
            arg_keys = arg1.keys()

        for key in chain(kwargs.keys(), arg_keys):
            self._index(key)

        super().update(arg1, **kwargs)

    def unsorted_key(self, key: "KeyLike") -> "KeyLike | None":
        """Return `key` with its original or unsorted dimensions."""
        k = _key_arg(key)
        return self._unsorted.get(k.sorted if isinstance(k, Key) else k)

    def full_key(self, name_or_key: "KeyLike") -> "KeyLike | None":
        """Return `name_or_key` with its full dimensions."""
        return self._full.get(Key(name_or_key).drop_all())

    def infer(self, key: str | Key, dims: Iterable[str] = []) -> "KeyLike | None":
        """Infer a `key`.

        Parameters
        ----------
        dims : list of str, optional
            Drop all but these dimensions from the returned key(s).

        Returns
        -------
        str
            If `key` is not found in the Graph.
        .Key
            `key` with either its full dimensions (cf. :meth:`full_key`) or, if `dims`
            are given, with only these dims.
        """
        result = self.unsorted_key(key) or key

        if isinstance(key, str) or not key.dims:
            # Find the full-dimensional key
            result = self.full_key(result) or ""

        if not isinstance(result, Key):
            return result or key

        # Drop all but `dims`
        if dims:
            result = result.drop(*(set(result.dims) - set(dims)))

        return result
