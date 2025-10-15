from importlib.metadata import version, PackageNotFoundError
# import your win32-specific modules here if they exist (e.g., from . import utils)

try:
    __version__ = version("win32interfaces")
except PackageNotFoundError:
    # Fallback for when the package is not installed
    __version__ = "0.1.0" 