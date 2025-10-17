from __future__ import annotations

try:
    import importlib.metadata as version_reader
except ImportError:
    import importlib_metadata as version_reader

try:
    __version__ = version_reader.version("sibi-dst")
except version_reader.PackageNotFoundError:
    __version__ = "unknown"

from sibi_dst.df_helper import *
from sibi_dst.osmnx_helper import *
from sibi_dst.geopy_helper import *
from sibi_dst import utils as sibiutils


__all__ = [
    "__version__",
    "DfHelper",
    "ParquetArtifact",
    "ParquetReader",
    "ArtifactUpdaterMultiWrapperAsync",
    "sibiutils"
]
