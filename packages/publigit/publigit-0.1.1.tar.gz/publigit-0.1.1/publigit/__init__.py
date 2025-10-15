from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("publigit")
except PackageNotFoundError:
    __version__ = "0.0.0"
__all__ = ["__version__"]