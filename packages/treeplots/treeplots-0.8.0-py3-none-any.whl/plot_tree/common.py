from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

ROOT_PATH = Path(__file__).resolve().parent.parent

__distribution_name = "treeplots"

try:
    PACKAGE_VERSION = version(__distribution_name)
except PackageNotFoundError:
    PACKAGE_VERSION = "unknown"
