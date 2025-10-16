"""Helpers to locate and load the external ``libchalk`` shared library.

This module is used by ``libchalk`` to support the "headless" wheel
variant where the compiled extension is supplied by the environment instead of
being bundled inside the package.  The loader searches a small, well-defined
set of locations so that users can control where the binary lives without
modifying ``sys.path`` manually.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, Iterator, Sequence

__all__ = [
    "ENV_PATH_OVERRIDE",
    "resolve_libchalk_path",
    "load_libchalk_extension",
]

ENV_PATH_OVERRIDE = "CHALKDF_LIBCHALK_PATH"

# Normal CPython exposes several suffixes for extension modules (per platform).
_EXTENSION_SUFFIXES: tuple[str, ...] = tuple(
    dict.fromkeys(importlib.machinery.EXTENSION_SUFFIXES + [".so", ".dylib", ".pyd"])
)


class LibchalkNotFoundError(ImportError):
    """Raised when the loader cannot locate a suitable shared library."""


def _candidate_basenames() -> Sequence[str]:
    return ("libchalk", "libchalk_release", "libchalk_debug")


def _looks_like_extension(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suffix) for suffix in _EXTENSION_SUFFIXES)


def _iter_directory_candidates(directory: Path) -> Iterator[Path]:
    if not directory.is_dir():
        return

    seen: set[Path] = set()
    for base in _candidate_basenames():
        for suffix in _EXTENSION_SUFFIXES:
            candidate = (directory / f"{base}{suffix}").resolve()
            if candidate.is_file() and candidate not in seen:
                seen.add(candidate)
                yield candidate

    # Fallback for filenames that inject build metadata (e.g. ``libchalk_v2.so``).
    for child in directory.glob("libchalk*"):
        resolved = child.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        if _looks_like_extension(resolved):
            seen.add(resolved)
            yield resolved


def _split_os_path(value: str) -> list[str]:
    return [chunk for chunk in value.split(os.pathsep) if chunk]


def _iter_search_directories(env: os._Environ[str], package_dir: Path) -> Iterator[tuple[str, Path]]:
    # 1. Adjacent locations to the package itself (covers the bundled wheel).
    yield ("package", package_dir)
    yield ("package_parent", package_dir.parent)

    # 2. Standard dynamic library search paths.
    for var in ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
        value = env.get(var)
        if not value:
            continue
        for chunk in _split_os_path(value):
            yield (var, Path(chunk).expanduser())

    # 3. Finally, fall back to ``sys.path`` entries so virtualenv/site-packages
    # directories are covered without a dedicated override.
    for entry in sys.path:
        try:
            resolved = Path(entry).expanduser().resolve()
        except (TypeError, ValueError, OSError):
            continue
        yield ("sys.path", resolved)


def _collect_candidate_paths(
    *,
    env: os._Environ[str] | None = None,
    sys_path: Iterable[str] | None = None,
    search_hint: Iterable[Path] | None = None,
) -> list[Path]:
    """Return candidate shared objects in the order they should be attempted."""

    env = os.environ if env is None else env
    package_dir = Path(__file__).resolve().parent
    sys_path_iterable = list(sys.path if sys_path is None else sys_path)

    override_value = env.get(ENV_PATH_OVERRIDE)
    if override_value:
        override_path = Path(override_value).expanduser()
        if override_path.is_file():
            if not _looks_like_extension(override_path):
                raise LibchalkNotFoundError(
                    f"{ENV_PATH_OVERRIDE}={override_value!r} is not a recognised libchalk shared object"
                )
            return [override_path.resolve()]
        if override_path.is_dir():
            matches = list(_iter_directory_candidates(override_path))
            if matches:
                return matches
            raise LibchalkNotFoundError(
                f"{ENV_PATH_OVERRIDE} directory {override_path!s} does not contain a libchalk shared object"
            )
        raise LibchalkNotFoundError(f"{ENV_PATH_OVERRIDE}={override_value!r} does not exist")

    search_queue: list[tuple[str, Path]] = []
    seen_dirs: set[Path] = set()

    extra_directories: list[Path] = [package_dir / "_lib", package_dir.parent / "_lib"]

    for label, directory in _iter_search_directories(env, package_dir):
        if label == "sys.path":
            continue
        resolved = directory.resolve()
        if resolved not in seen_dirs:
            seen_dirs.add(resolved)
            search_queue.append((label, resolved))

    extra_entries: list[tuple[str, Path]] = []
    for extra_dir in extra_directories:
        try:
            resolved = extra_dir.resolve()
        except OSError:
            continue
        if resolved not in seen_dirs:
            seen_dirs.add(resolved)
            extra_entries.append(("package_extra", resolved))

    search_queue = extra_entries + search_queue

    if search_hint:
        for path in search_hint:
            try:
                resolved = Path(path).resolve()
            except OSError:
                continue
            if resolved not in seen_dirs:
                seen_dirs.add(resolved)
                search_queue.append(("hint", resolved))

    for entry in sys_path_iterable:
        try:
            resolved = Path(entry).resolve()
        except (TypeError, ValueError, OSError):
            continue
        if resolved not in seen_dirs:
            seen_dirs.add(resolved)
            search_queue.append(("sys.path", resolved))

    candidate_files: list[Path] = []
    for _, directory in search_queue:
        if directory.is_file():
            if _looks_like_extension(directory):
                candidate_files.append(directory)
            continue
        candidate_files.extend(_iter_directory_candidates(directory))

    return candidate_files


def resolve_libchalk_path(
    *,
    env: os._Environ[str] | None = None,
    sys_path: Iterable[str] | None = None,
    search_hint: Iterable[Path] | None = None,
) -> Path:
    """Return the first candidate path for the ``libchalk`` shared object."""

    candidates = _collect_candidate_paths(env=env, sys_path=sys_path, search_hint=search_hint)
    if candidates:
        return candidates[0]

    package_dir = Path(__file__).resolve().parent
    searched = [
        f"{label}:{path}" for label, path in _iter_search_directories(os.environ if env is None else env, package_dir)
    ]
    parts = [
        "Unable to locate the libchalk shared library.",
        "Searched: " + ", ".join(searched) if searched else "No candidate directories were reachable.",
    ]
    parts.append(f"Set {ENV_PATH_OVERRIDE} to the directory (or exact file) that contains libchalk.cpython-<abi>.so.")
    raise LibchalkNotFoundError(" ".join(parts))


def load_libchalk_extension(fullname: str) -> ModuleType:
    """Load the ``libchalk`` extension module located by :func:`resolve_libchalk_path`."""

    existing = sys.modules.get(fullname)
    if isinstance(existing, ModuleType) and getattr(existing, "__spec__", None):
        return existing

    candidates = _collect_candidate_paths()
    loader_errors: list[str] = []

    for shared_object in candidates:
        spec = importlib.util.spec_from_file_location(fullname, shared_object)
        if spec is None or not isinstance(spec.loader, importlib.machinery.ExtensionFileLoader):
            loader_errors.append(f"{shared_object} is not a valid extension module")
            continue

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[fullname] = module
            spec.loader.exec_module(module)
        except ImportError as exc:  # pragma: no cover - depends on local interpreter
            loader_errors.append(f"{shared_object}: {exc}")
            sys.modules.pop(fullname, None)
            continue
        else:
            break
    else:
        searched = ", ".join(str(path) for path in candidates) or "<none>"
        details = "; ".join(loader_errors) if loader_errors else "no suitable shared object found"
        raise ImportError(
            (
                "Unable to load libchalk. Tried: "
                f"{searched}. Errors: {details}. Install a compatible libchalk binary (e.g. via "
                '`pip install "chalkdf[chalkpy]"`) or rebuild it.'
            ),
            name=fullname,
        )

    # Ensure that Python treats the module as a package so that submodules
    # provided by the binary remain importable.
    package_paths: list[str] = []
    parent_dir = shared_object.parent
    if parent_dir.is_dir():
        package_paths.append(str(parent_dir))
    module.__dict__.setdefault("__path__", package_paths)

    return module
