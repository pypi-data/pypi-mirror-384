"""Python client for Spiral"""

# This is here to make sure we load the native extension first
from spiral import _lib

# Eagerly import the Spiral library
assert _lib, "Spiral library"

from spiral.client import Spiral  # noqa: E402
from spiral.core.client import Shard, ShuffleConfig  # noqa: E402
from spiral.dataloader import SpiralDataLoader, World  # noqa: E402
from spiral.iceberg import Iceberg  # noqa: E402
from spiral.key_space_index import KeySpaceIndex  # noqa: E402
from spiral.project import Project  # noqa: E402
from spiral.scan import Scan  # noqa: E402
from spiral.snapshot import Snapshot  # noqa: E402
from spiral.table import Table  # noqa: E402
from spiral.text_index import TextIndex  # noqa: E402
from spiral.transaction import Transaction  # noqa: E402

__all__ = [
    "Spiral",
    "Project",
    "Table",
    "Snapshot",
    "Transaction",
    "Scan",
    "Shard",
    "ShuffleConfig",
    "TextIndex",
    "KeySpaceIndex",
    "SpiralDataLoader",
    "World",
    "Iceberg",
]
