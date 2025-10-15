import logging
import re
from importlib import import_module

import pytest

from genno import Computer, Key, MissingKeyError, config, configure
from genno.compat.pyam import HAS_PYAM
from genno.config import HANDLERS, ConfigHandler, handles


def test_deprecated_store_global(recwarn):
    config.STORE.add("FOO")

    # Warning is emitted here since Computer.__init__() calls parse_config()
    with pytest.warns(DeprecationWarning, match="genno.config.STORE"):
        c = Computer()

    # STORE was emptied, converted to handler in HANDLERS
    assert 0 == len(config.STORE)

    # Value is handled correctly
    c.configure(FOO="BAR")
    assert "BAR" == c.graph["config"]["FOO"]

    # Restore state for other tests
    HANDLERS.pop("FOO")


def test_handlers():
    # Account for handlers in packages modules that may be installed in the user's
    # testing environment
    third_party_handlers = 0
    try:
        import_module("ixmp")
    except ImportError:
        pass
    else:  # pragma: no cover
        third_party_handlers += 2

    # Expected config handlers are available
    assert 11 + (1 * HAS_PYAM) + third_party_handlers == len(HANDLERS)

    # Handlers are all callable
    for key, ch in HANDLERS.items():
        assert isinstance(key, str) and isinstance(ch, ConfigHandler)


@pytest.mark.parametrize(
    "name",
    [
        "config-aggregate0.yaml",
        "config-aggregate1.yaml",
        pytest.param(
            "config-aggregate2.yaml", marks=pytest.mark.xfail(raises=MissingKeyError)
        ),
        "config-combine.yaml",
        "config-general0.yaml",
        pytest.param(
            "config-general1.yaml", marks=pytest.mark.xfail(raises=ValueError)
        ),
        "config-report.yaml",
        "config-units.yaml",
    ],
)
def test_file(test_data_path, name):
    """Test handling configuration file syntax using test data files."""
    c = Computer()

    # Set up test contents
    c.add(Key("X", list("abc")), None, sums=True)
    c.add(Key("Y", list("bcd")), None, sums=True)

    c.configure(path=test_data_path / name)


def test_general_infer_dims():
    """Test dimension inference in handling "general:" config items."""
    c = Computer()

    # Set up test contents
    c.add(Key("X", list("abcd")), None, sums=True)
    c.add(Key("Y", list("cefg")), None, sums=True)

    c.configure(general=[dict(comp="concat", key="Z:*:foo", inputs=["X", "Y"])])

    # Dimensions were inferred
    assert "Z:a-b-c-d-e-f-g:foo" in c


def test_global(test_data_path):
    configure(path=test_data_path / "config-units.yaml")

    with pytest.raises(
        RuntimeError, match="Cannot apply non-global configuration without a Computer"
    ):
        configure(path=test_data_path / "config-global.yaml")


def test_handles(caplog, monkeypatch):
    """:func:`handles` raises a warning when used twice."""
    monkeypatch.delitem(HANDLERS, "foo", raising=False)
    caplog.set_level(logging.DEBUG)

    @handles("foo")
    def foo1(c: Computer, info):
        """Test function; never executed."""

    assert len(caplog.messages) == 0

    @handles("foo")
    def foo2(c: Computer, info):
        """Test function; never executed."""

    assert 1 == len(caplog.messages)
    assert re.match(
        r"Override ConfigHandler\(key='foo', "
        "callback=<function test_handles.<locals>.foo1 [^>]*>, iterate=True, "
        r"discard=True\)",
        caplog.messages[0],
    )
