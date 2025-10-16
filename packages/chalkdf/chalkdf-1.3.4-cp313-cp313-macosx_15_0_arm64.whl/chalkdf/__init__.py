"""Public entry points for the :mod:`chalkdf` library.

This module exposes the :class:`~chalkdf.dataframe.DataFrame` type along with
expression helpers and testing utilities so that users can simply ``import
chalkdf`` and access the core API.
"""

from __future__ import annotations

import sys

from ._libchalk_bootstrap import LibchalkNotFoundError, load_libchalk_extension

try:
    load_libchalk_extension("libchalk")
except (LibchalkNotFoundError, ImportError) as exc:  # pragma: no cover - depends on optional binary
    raise ImportError(
        "libchalk failed to load. Install a libchalk shared library built for Python "
        f'{sys.version_info.major}.{sys.version_info.minor} (e.g. `pip install "chalkdf"` (non-headless)).'
    ) from exc

from libchalk.chalktable import AggExpr, Expr

from .dataframe import DataFrame
from .lazyframe import LazyFrame
from .testing import Testing

__all__ = ["DataFrame", "LazyFrame", "Expr", "AggExpr", "Testing"]
