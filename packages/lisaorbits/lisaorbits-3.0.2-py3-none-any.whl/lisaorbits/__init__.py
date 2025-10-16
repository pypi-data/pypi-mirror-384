"""LISA Orbits module."""

import importlib_metadata

from .oem import OEMOrbits
from .orbits import (
    LINKS,
    SC,
    EqualArmlengthOrbits,
    InterpolatedOrbits,
    KeplerianOrbits,
    Orbits,
    ResampledOrbits,
    StaticConstellation,
)

# Automatically set by `poetry dynamic-versioning`
__version__ = "3.0.2"

try:
    metadata = importlib_metadata.metadata("lisaorbits").json
    __author__ = metadata["author"]
    __email__ = metadata["author_email"]
except importlib_metadata.PackageNotFoundError:
    pass
