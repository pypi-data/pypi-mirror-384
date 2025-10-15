import pytest

from genno import Key, Keys, KeySeq
from genno.core.key import iter_keys, single_key
from genno.testing import raises_or_warns


def test_key():
    k1 = Key("foo", ["a", "b", "c"])
    k2 = Key("bar", ["d", "c", "b"])

    # String
    assert str(k1) == "foo:a-b-c"

    # Representation
    assert repr(k1) == "<foo:a-b-c>"

    # Key hashes the same as its string representation
    assert hash(k1) == hash("foo:a-b-c")

    # Key compares equal to its string representation
    assert k1 == "foo:a-b-c"

    # product:
    assert Key.product("baz", k1, k2) == Key("baz", ["a", "b", "c", "d"])
    assert Key.product("baz", str(k1), str(k2)) == Key("baz", ["a", "b", "c", "d"])

    # iter_sums: Number of partial sums for a 3-dimensional quantity
    assert sum(1 for a in k1.iter_sums()) == 7

    # Key with name and tag but no dimensions
    assert Key("foo", tag="baz") == "foo::baz"


_invalid = pytest.raises(ValueError, match="Invalid key expression")

CASES = (
    ("foo", Key("foo")),
    ("foo:", Key("foo")),
    ("foo::", Key("foo")),
    ("foo::bar", Key("foo", tag="bar")),
    ("foo::bar+baz", Key("foo", tag="bar+baz")),
    ("foo:a-b", Key("foo", "ab")),
    ("foo:a-b:", Key("foo", "ab")),
    ("foo:a-b:bar", Key("foo", "ab", "bar")),
    # Weird but not invalid
    ("foo::++", Key("foo", tag="++")),
    # Invalid
    (":", _invalid),
    ("::", _invalid),
    ("::bar", _invalid),
    (":a-b:bar", _invalid),
    ("foo:a-b-", _invalid),
    # Bad arguments
    (42.1, pytest.raises(TypeError)),
)


class TestKey:
    @pytest.mark.parametrize("value, expected", CASES)
    def test_init0(self, value, expected) -> None:
        with raises_or_warns(expected, None):
            assert expected == Key(value)

    @pytest.mark.parametrize(
        "args, expected",
        (
            ((Key("foo:a-b-c"), [], "t2"), Key("foo:a-b-c:t2")),
            pytest.param(
                (Key("foo:a-b-c:t1"), [], "t2"),
                None,
                marks=pytest.mark.xfail(raises=ValueError),
            ),
            pytest.param(
                (Key("foo:a-b-c"), "d e f".split()),
                None,
                marks=pytest.mark.xfail(raises=ValueError),
            ),
        ),
    )
    def test_init1(self, args, expected):
        assert expected == Key(*args)

    @pytest.mark.parametrize("value, expected", CASES)
    def test_from_str_or_key0(self, value, expected) -> None:
        with raises_or_warns(expected, FutureWarning, match="no longer necessary"):
            assert expected == Key.from_str_or_key(value)

    @pytest.mark.parametrize(
        "kwargs, value, expected",
        (
            (dict(drop="b"), "foo:a-b-c", Key("foo:a-c")),
            (dict(drop="b", append="d"), "foo:a-b-c", Key("foo:a-c-d")),
            (dict(drop="b", tag="t2"), "foo:a-b-c:t1", Key("foo:a-c:t1+t2")),
        ),
    )
    def test_from_str_or_key1(self, kwargs, value, expected):
        assert expected == Key.from_str_or_key(value, **kwargs)

    def test_drop(self):
        key = Key("out:nl-t-yv-ya-m-nd-c-l-h-hd")
        assert "out:t-yv-ya-c-l" == key.drop("h", "hd", "m", "nd", "nl")

    def test_eq(self):
        assert False is (Key("x:a-b-c") == 3.4)

    def test_generated(self) -> None:
        k = Key("A:x")

        # Generate some related keys
        k[3]
        k["baz"]
        k[2]
        k["bar"]
        k[1]

        exp = tuple(map(Key, ["A:x:3", "A:x:baz", "A:x:2", "A:x:bar", "A:x:1"]))
        assert exp == k.generated

    def test_getitem(self) -> None:
        k = Key("foo:x-y-z:bar")

        # __getitem__ works with str argument
        assert "foo:x-y-z:bar+baz" == k["baz"]
        assert "foo:x-y-z:bar+qux" == k["qux"]

        # __getitem__ works with int argument
        assert "foo:x-y-z:bar+0" == k[0]
        assert "foo:x-y-z:bar+1" == k[1]

        assert "foo:x-y-z:bar+2" == next(k)
        assert "foo:x-y-z:bar+2" == k.last

    def test_hash(self) -> None:
        k1 = Key("x:a-b-c")
        k2 = Key("x:c-b-a")

        d = {k1: None}

        assert k2 in d

    def test_operations(self):
        key = Key("x:a-b-c")

        # __add__: Add a tag
        assert "x:a-b-c:foo" == key + "foo"
        # Associative: (key + "foo") is another key that supports __add__
        assert "x:a-b-c:foo+bar" == key + "foo" + "bar"

        # __mul__: add a dimension
        assert "x:a-b-c-d" == key * "d"

        # Add multiple dimensions
        assert "x:a-b-c-d-e" == key * ("d", "e")
        assert "x:a-b-c-d-e" == key * Key("foo", "de")

        # Existing dimension → no change
        assert key == key * "c"

        # __truediv__: drop a dimension
        assert "x:a-c" == key / "b"

        # Drop multiple dimensions
        assert "x:b" == key / ("a", "c")
        assert "x:b" == key / Key("foo", "ac")

        # Invalid
        with pytest.raises(TypeError):
            key + 1.1
        with pytest.raises(TypeError):
            key * 2.2
        with pytest.raises(TypeError):
            key / 3.3

    def test_sorted(self) -> None:
        k1 = Key("foo", "abc")
        k2 = Key("foo", "cba")

        # Keys with same dimensions, ordered differently, compare equal
        assert k1 == k2

        # Ordered returns a key with sorted dimensions
        assert k1.dims == k2.sorted.dims

        # Keys compare equal to an equivalent string and to one another
        assert k1 == "foo:b-a-c" == k2 == "foo:b-c-a"

        # Keys hash equal to a string with sorted dimensions
        assert hash("foo:a-b-c") == hash(k1) == hash(k2)

        # `k2` does not hash equal to its own (unsorted) string representation
        assert hash(k2) != hash(str(k2))


class TestKeys:
    """:class:`.Keys` behaves as expected."""

    @pytest.fixture(scope="function")
    def keys(self) -> Keys:
        return Keys(foo=Key("foo:a-b-c"), bar="bar:a-b-c")

    def test_init(self, keys: Keys) -> None:
        """:class:`.Keys` can be initialized with :any:`.KeyLike`."""
        assert isinstance(keys.foo, Key) and isinstance(keys.bar, Key)

    def test_delattr(self, keys: Keys) -> None:
        """Keys can be deleted."""
        del keys.bar

        with pytest.raises(AttributeError):
            keys.bar

    def test_getattr(self, keys: Keys) -> None:
        """Keys can be accessed and used."""
        assert "foo:a-b-c:0" == keys.foo[0]

        # Binary operations work
        assert "foo:a-c" == keys.foo / "b"
        assert "foo:a-b-c-d" == keys.foo * "d"
        assert "foo:a-b-c:tag" == keys.foo + "tag"

    def test_repr(self, keys: Keys) -> None:
        keys.baz = Key("it's confusing:m-n-o-p")
        # repr() does not include the Key.name, but the name in the namespace
        assert "<3 keys: bar baz foo>" == repr(keys)

    def test_setattr(self, keys: Keys) -> None:
        """Keys can be set and updated."""
        # Update an existing name
        keys.bar = Key("bar:x-y-z")
        # Update occurred
        assert "bar:x-y-z" == keys.bar

        # New key
        keys.baz = Key("baz:c-b-a")
        assert "baz:a-b-c" == keys.baz


class TestKeySeq:
    @pytest.fixture
    def ks(self) -> KeySeq:
        return KeySeq("foo:x-y-z:bar")

    def test_call(self, ks) -> None:
        assert "foo:x-y-z:bar+0" == ks()
        assert "foo:x-y-z:bar+1" == ks()
        assert "foo:x-y-z:bar+2" == ks()
        assert "foo:x-y-z:bar+2" == ks.prev

        # Continues from interruption
        ks[5]
        assert "foo:x-y-z:bar+6" == next(ks)

    def test_getitem(self, ks) -> None:
        assert "foo:x-y-z:bar+baz" == ks["baz"]
        assert "foo:x-y-z:bar+qux" == ks["qux"]
        assert "foo:x-y-z:bar+qux" == ks.prev
        assert "foo:x-y-z:bar+0" == next(ks)
        assert "foo:x-y-z:bar+0" == ks.prev

    def test_keys(sefl, ks) -> None:
        ks["foo"]
        ks[5]
        next(ks)
        ks["baz"]
        ks[0]

        # .keys preserves order of creation
        assert ("foo", 5, 6, "baz", 0) == tuple(ks.keys)

    def test_next(self, ks) -> None:
        assert "foo:x-y-z:bar+0" == next(ks)
        assert "foo:x-y-z:bar+1" == next(ks)
        assert "foo:x-y-z:bar+2" == next(ks)
        assert "foo:x-y-z:bar+2" == ks.prev

        # Continues from interruption
        ks[5]
        assert "foo:x-y-z:bar+6" == next(ks)

    def test_repr(self, ks) -> None:
        assert "<KeySeq from 'foo:x-y-z:bar'>" == repr(ks)

    def test_key_attrs(self, ks) -> None:
        assert "foo" == ks.name
        assert ("x", "y", "z") == ks.dims
        assert "bar" == ks.tag

    def test_key_ops(self, ks) -> None:
        # __add__
        assert "foo:x-y-z:bar+baz" == (ks + "baz").base

        # __mul__
        assert "foo:w-x-y-z:bar" == (ks * "w").base

        # __sub__
        assert "foo:x-y-z" == (ks - "bar").base
        with pytest.raises(ValueError):
            ks - "qux"

        # __truediv__
        assert "foo:x-z:bar" == (ks / "y").base


def test_gt_lt() -> None:
    """Test :meth:`Key.__gt__` and :meth:`Key.__lt__`."""
    k = Key("foo", "abd")
    assert k > "foo:a-b-c"
    assert k > Key("foo", "abc")
    assert k < "foo:a-b-e"
    assert k < Key("foo", "abe")

    # Comparison with other types not supported
    with pytest.raises(TypeError):
        assert k < 1.1

    with pytest.raises(TypeError):
        assert k > 1.1


def test_iter_keys() -> None:
    # Non-iterable
    with pytest.raises(TypeError):
        next(iter_keys(1.2))  # type: ignore [arg-type]

    # Iterable containing non-keys
    with pytest.raises(TypeError):
        list(iter_keys([Key("a"), Key("b"), 1.2]))  # type: ignore [arg-type]


def test_single_key() -> None:
    # Single key is unpacked
    k = Key("a")
    result = single_key((k,))
    assert k is result

    # Tuple containing 1 non-key
    with pytest.raises(TypeError):
        single_key((1.2,))  # type: ignore [arg-type]

    # Tuple containing >1 Keys
    with pytest.raises(TypeError):
        single_key((k, k))

    # Empty iterable
    with pytest.raises(TypeError):
        single_key([])  # type: ignore [arg-type]
