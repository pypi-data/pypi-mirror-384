import dataclasses
import functools
import os
from typing import Any

import vortex as vx

from spiral.core.client import Shard


# Fake streaming.base.format.base.reader.FileInfo
# Dataset manages decompression instead of the Stream in MDS.
# So we return our own fake FileInfo that has None for compressed file.
@dataclasses.dataclass
class FileInfo:
    basename: str
    hashes: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def bytes(self):
        raise NotImplementedError("FileInfo.bytes should NOT be called.")


class SpiralReader:
    """
    An MDS (streaming) compatible Reader.
    """

    def __init__(self, shard: Shard, basepath):
        self._shard = shard
        if shard.cardinality is None:
            raise ValueError("Shard cardinality must be known for `streaming`.")
        self._cardinality = shard.cardinality
        self._basepath = basepath
        self._scan: vx.RepeatedScan | None = None

    @property
    def shard(self) -> Shard:
        return self._shard

    @property
    def size(self):
        """Get the number of samples in this shard.

        Returns:
            int: Sample count.
        """
        return self._cardinality

    @property
    def samples(self):
        """Get the number of samples in this shard.

        Returns:
            int: Sample count.
        """
        return self._cardinality

    def __len__(self) -> int:
        """Get the number of samples in this shard.

        Returns:
            int: Sample count.
        """
        return self._cardinality

    @property
    def file_pairs(self) -> list[tuple[FileInfo, FileInfo | None]]:
        """Get the infos from raw and compressed file.

        MDS uses this because dataset manages decompression of the shards, not stream...
        """
        return [(FileInfo(basename=self.filename), None)]

    def get_max_size(self) -> int:
        """Get the full size of this shard.

        "Max" in this case means both the raw (decompressed) and zip (compressed) versions are
        resident (assuming it has a zip form). This is the maximum disk usage the shard can reach.
        When compressed was used, even if keep_zip is ``False``, the zip form must still be
        resident at the same time as the raw form during shard decompression.

        Returns:
            int: Size in bytes.
        """
        # TODO(marko): This is used to check cache limit is possible...
        return 0

    @functools.cached_property
    def filename(self) -> str:
        """Used by SpiralStream to identify shard's file-on-disk, if it exists."""
        # TODO(marko): This might be too long...
        return (
            bytes(self._shard.key_range.begin).hex()
            + "_"
            + bytes(self._shard.key_range.end).hex()
            + "_"
            + str(self._shard.cardinality)
            + ".vortex"
        )

    @functools.cached_property
    def filepath(self) -> str:
        """Full path to the shard's file-on-disk, if it exists."""
        return os.path.join(self._basepath, self.filename)

    def evict(self) -> int:
        """Remove all files belonging to this shard."""

        # Clean up the scan handle first. This will make sure memory is freed.
        self._scan = None

        # Try to evict file.
        try:
            stat = os.stat(self.filepath)
            os.remove(self.filepath)
            return stat.st_size
        except FileNotFoundError:
            # Nothing to evict.
            return 0

    def __getitem__(self, item):
        return self.get_item(item)

    def get_item(self, idx: int) -> dict[str, Any]:
        if self._scan is None:
            # TODO(marko): vx.open should throw FileNotFoundError instead of
            #   ValueError: No such file or directory (os error 2)
            # Check if shard is ready on disk. This must throw FileNotFoundError.
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Shard not found: {self.filepath}")
            self._scan = vx.open(self.filepath, without_segment_cache=True).to_repeated_scan()
        return self._scan.scalar_at(idx).as_py()
