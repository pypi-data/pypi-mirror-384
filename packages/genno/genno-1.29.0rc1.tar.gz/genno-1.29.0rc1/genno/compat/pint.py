"""Compatibility code for :mod:`pint`.

Notes:

- In unit expressions that contain multiple errors (e.g. undefined units *and* invalid
  syntax), the exact exception raised by pint can sometimes vary between releases.
- In pint 0.17, DefinitionSyntaxError is a subclass of SyntaxError.
  In pint 0.20, it is a subclass of ValueError.
- In pint <0.22, certain expressions raise DefinitionSyntaxError.
  In pint ≥0.22, they instead raise AssertionError.
"""

from importlib.metadata import version

import pint

try:
    PintError: tuple[type[Exception], ...] = (pint.PintError,)
    ApplicationRegistry: type = pint.ApplicationRegistry
except AttributeError:  # pragma: no cover
    # Older versions of pint, e.g. 0.17
    PintError = (type("PintError", (Exception,), {}), pint.DefinitionSyntaxError)
    ApplicationRegistry = pint.UnitRegistry

if version("Pint") >= "0.22":
    PintError = PintError + (AssertionError,)

__all__ = [
    "ApplicationRegistry",
    "PintError",
]
