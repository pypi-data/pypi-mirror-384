"""Module providing __init__ functionality."""
from matrice_common.utils import dependencies_check

base = [
    "httpx",
    "fastapi", 
    "uvicorn",
    "pillow",
    "confluent_kafka[snappy]",
    "aiokafka",
    "aiohttp",
    "filterpy",
    "scipy",
    "scikit-learn", 
    "matplotlib",
    "scikit-image",
    "python-snappy",
    "pyyaml",
    "imagehash",
]

# Install base dependencies first
dependencies_check(base)

# Helper to attempt installation and verify importability
def _install_and_verify(pkg: str, import_name: str):
    """Install a package expression and return True if the import succeeds."""
    if dependencies_check([pkg]):
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
    return False

if not dependencies_check(["opencv-python"]):
    dependencies_check(["opencv-python-headless"])
