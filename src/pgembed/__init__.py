from ._commands import *  # noqa: F403
from .postgres_server import PostgresServer, get_server
from pathlib import Path
from typing import Optional
import logging
import importlib.util

__all__ = [
    "PostgresServer",
    "get_server",
    "has_extension",
    "list_extensions",
    "get_extension_create_name",
    "get_extension_path",
]

_logger = logging.getLogger("pgembed")


def _get_pkg_path():
    spec = importlib.util.find_spec("pgembed")
    if spec and spec.submodule_search_locations:
        return Path(spec.submodule_search_locations[0])
    return Path(__file__).parent


EXTENSION_LIB_PATH = _get_pkg_path() / "pginstall" / "lib"
EXTENSION_POSTGRES_LIB_PATH = EXTENSION_LIB_PATH / "postgresql"

AVAILABLE_EXTENSIONS = {}

EXTENSION_PACKAGES = {
    "pgvector": "pgembed_pgvector",
    "pgvectorscale": "pgembed_pgvectorscale",
    "pgtextsearch": "pgembed_pgtextsearch",
    "pg_search": "pgembed_pgsearch",
    "pgsql_http": "pgembed_pgsql_http",
}

EXTENSION_SO_FILES = {
    "pgvector": ("vector.so", "vector.dylib", "vector.dll"),
    "pgvectorscale": (
        "vectorscale-0.9.0.so",
        "vectorscale-0.9.0.dylib",
        "vectorscale-0.5.1.so",
        "vectorscale-0.5.1.dylib",
        "vectorscale.so",
        "vectorscale.dylib",
    ),
    "pgtextsearch": ("pg_textsearch.so", "pg_textsearch.dylib"),
    "pg_search": ("pg_search.so", "pg_search.dylib"),
    "pg_duckdb": ("pg_duckdb.so", "pg_duckdb.dylib"),
    "pgsql_http": ("http.so", "http.dylib"),
}

EXTENSION_NAMES = (
    "pgvector",
    "pgvectorscale",
    "pgtextsearch",
    "pg_search",
    "pg_duckdb",
    "pgsql_http",
)


def _find_bundled_so(name: str) -> Optional[Path]:
    so_files = EXTENSION_SO_FILES.get(name, ())
    if isinstance(so_files, str):
        so_files = (so_files,)
    for lib_dir in (EXTENSION_POSTGRES_LIB_PATH, EXTENSION_LIB_PATH):
        for so_file in so_files:
            candidate = lib_dir / so_file
            if candidate.exists():
                return candidate
    return None


def _detect_extensions():
    global AVAILABLE_EXTENSIONS

    for name in EXTENSION_NAMES:
        pkg_name = EXTENSION_PACKAGES.get(name)
        try:
            if pkg_name:
                ext_pkg = __import__(pkg_name)
                if hasattr(ext_pkg, "install_into_pgembed"):
                    try:
                        ext_pkg.install_into_pgembed()
                    except Exception as exc:
                        _logger.debug(
                            f"Failed to install split extension {pkg_name} into pginstall: {exc}"
                        )
                ext_path = ext_pkg.get_extension_path()
                if ext_path and ext_path.exists():
                    AVAILABLE_EXTENSIONS[name] = True
                    _logger.info(f"Detected extension from package {pkg_name}: {name}")
                    continue
        except ImportError:
            pass

        bundled_path = _find_bundled_so(name)
        if bundled_path is not None:
            AVAILABLE_EXTENSIONS[name] = True
            _logger.info(f"Detected extension from bundled lib: {name}")
            continue

        AVAILABLE_EXTENSIONS[name] = False


def has_extension(name: str) -> bool:
    """Check if a specific extension is available.

    Args:
        name: Extension name (e.g., 'pgvector', 'pgvectorscale', 'pgtextsearch', 'pg_search', 'pg_duckdb')

    Returns:
        True if the extension is available, False otherwise.
    """
    return AVAILABLE_EXTENSIONS.get(name, False)


def list_extensions() -> dict:
    """Return a dictionary of available extensions.

    Returns:
        Dict mapping extension names to availability (True/False)
    """
    return AVAILABLE_EXTENSIONS.copy()


def get_extension_create_name(name: str) -> str:
    """Get the SQL extension creation name for an extension.

    Args:
        name: Extension name (e.g., 'pgvector', 'pgtextsearch')

    Returns:
        The SQL name to use when creating the extension.
    """
    create_names = {
        "pgvector": "vector",
        "pgvectorscale": "vectorscale",
        "pgtextsearch": "pg_textsearch",
        "pg_search": "pg_search",
        "pg_duckdb": "pg_duckdb",
        "pgsql_http": "http",
    }
    return create_names.get(name, name)


def get_extension_path(name: str) -> Optional[Path]:
    """Get the path to an extension .so/.dylib file.

    Args:
        name: Extension name (e.g., 'pgvector', 'pgtextsearch')

    Returns:
        Path to the shared library file, or None if not available.
    """
    pkg_name = EXTENSION_PACKAGES.get(name)
    if pkg_name:
        try:
            ext_pkg = __import__(pkg_name)
            ext_path = ext_pkg.get_extension_path()
            if ext_path and ext_path.exists():
                return ext_path
        except ImportError:
            pass

    return _find_bundled_so(name)


_detect_extensions()
