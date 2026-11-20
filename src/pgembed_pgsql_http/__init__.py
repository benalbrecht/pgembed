__version__ = "0.1.8"

EXTENSION_NAME = "pgsql_http"
EXTENSION_SO_FILES = ("http.so", "http.dylib")
EXTENSION_CREATE = "http"


def get_extension_path():
    from pathlib import Path

    pkg_dir = Path(__file__).parent
    for filename in EXTENSION_SO_FILES:
        so_path = pkg_dir / filename
        if so_path.exists():
            return so_path

    try:
        import pgembed

        base_lib = pgembed.EXTENSION_LIB_PATH
        for candidate_dir in (base_lib / "postgresql", base_lib):
            for filename in EXTENSION_SO_FILES:
                bundled = candidate_dir / filename
                if bundled.exists():
                    return bundled
    except ImportError:
        pass

    return None


def get_extension_share_path():
    from pathlib import Path

    pkg_dir = Path(__file__).parent
    if (pkg_dir / f"{EXTENSION_CREATE}.control").exists():
        return pkg_dir

    try:
        import pgembed

        for share_rel in (
            Path("share") / "postgresql" / "extension",
            Path("share") / "extension",
        ):
            base_share = Path(__file__).parent / "pginstall" / share_rel
            if (base_share / f"{EXTENSION_CREATE}.control").exists():
                return base_share

            base_share = pgembed.EXTENSION_LIB_PATH.parent / share_rel
            if (base_share / f"{EXTENSION_CREATE}.control").exists():
                return base_share
    except ImportError:
        pass
    return None


def install_into_pgembed():
    """Copy split-wheel extension artifacts into pgembed's pginstall directories if present."""
    from pathlib import Path
    import shutil

    try:
        import pgembed
    except ImportError:
        return False

    pkg_dir = Path(__file__).parent
    lib_dir = pgembed.EXTENSION_LIB_PATH
    if not lib_dir.exists():
        return False

    target_lib = lib_dir / "postgresql" if (lib_dir / "postgresql").exists() else lib_dir
    installed_any = False

    for filename in EXTENSION_SO_FILES:
        src = pkg_dir / filename
        if src.exists():
            dst = target_lib / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            installed_any = True

    pginstall_dir = lib_dir.parent
    share_candidates = [
        pginstall_dir / "share" / "postgresql" / "extension",
        pginstall_dir / "share" / "extension",
    ]
    target_share = next((d for d in share_candidates if d.exists()), None)
    if target_share is not None:
        for pattern in ("http.control", "http--*.sql"):
            for src in pkg_dir.glob(pattern):
                dst = target_share / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
                installed_any = True

    return installed_any
