try:
    from importlib.metadata import version, PackageNotFoundError
except Exception:  # pragma: no cover
    version = None
    class PackageNotFoundError(Exception):  # pragma: no cover
        pass

def _get_version() -> str:
    if version is None:
        return "0+unknown"
    try:
        return version("zz-tools")
    except PackageNotFoundError:
        return "0+unknown"

__version__ = _get_version()
