import os
import tempfile
from typing import TYPE_CHECKING

import numpy as np

from spiral.core.client import Shard
from spiral.core.table import Scan as CoreScan
from spiral.streaming_.reader import SpiralReader

if TYPE_CHECKING:
    from streaming.base.array import NDArray
    from streaming.base.format import Reader
    from streaming.base.world import World


class SpiralStream:
    """
    An MDS (streaming) compatible Stream.

    The stream does not extend the default Stream class, but it is compactible with its API.

    The stream is not registered with MDS, as the only way to construct the stream is through Spiral client.
    Stream can be passed to MDS's StreamingDataset in `streams` argument.
    """

    def __init__(
        self,
        scan: CoreScan,
        shards: list[Shard],
        cache_dir: str | None = None,
        shard_row_block_size: int | None = None,
    ):
        self._scan = scan
        # TODO(marko): Read shards only on world.is_local_leader in `get_shards` and materialize on disk.
        self._shards = shards
        self._shard_row_block_size = shard_row_block_size or 8192

        if cache_dir is not None:
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            if not os.path.isdir(cache_dir):
                raise ValueError(f"Cache dir {cache_dir} is not a directory.")
        else:
            cache_dir = tempfile.gettempdir()
        self._cache_dir = cache_dir

        # Enure split directory exists.
        os.makedirs(os.path.join(self._cache_dir, self.split), exist_ok=True)

    @property
    def local(self) -> str:
        # Dataset: Register/lookup our shared memory prefix and filelock root directory.
        return self._cache_dir

    @property
    def remote(self) -> str | None:
        # Dataset: Register/lookup our shared memory prefix and filelock root directory.
        return None

    @property
    def split(self) -> str:
        # Dataset: Register/lookup our shared memory prefix and filelock root directory.
        return "default"

    @classmethod
    def validate_weights(cls, streams) -> tuple[bool, bool]:
        from streaming.base.stream import Stream

        return Stream.validate_weights(streams)

    @classmethod
    def apply_weights(cls, streams, samples_per_stream, choose_per_epoch, seed) -> int:
        from streaming.base.stream import Stream

        return Stream.apply_weights(streams, samples_per_stream, choose_per_epoch, seed)

    def apply_default(self, default: dict):
        # Applies defaults from the StreamingDataset.
        # 'remote', 'local', 'split', 'download_retry', 'download_timeout', 'validate_hash', 'keep_zip'
        if default["split"] is not None:
            raise ValueError("SpiralStream does not support split, as the split is defined in the Scan.")

    def prepare_shard(self, shard: "Reader") -> int:
        """Ensure (download, validate, extract, etc.) that we have the given shard.

        Args:
            shard (Reader): Which shard.

        Returns:
            int: Change in cache usage.
        """
        if not isinstance(shard, SpiralReader):
            raise ValueError("Only SpiralReader is supported in SpiralStream")

        shard_path = os.path.join(self._cache_dir, self.split, shard.filename)
        if os.path.exists(shard_path):
            # Already exists.
            return 0

        # This method exists but it's hidden.
        self._scan._prepare_shard(
            shard_path,
            shard.shard.key_range,
            expected_cardinality=shard.shard.cardinality,
            shard_row_block_size=self._shard_row_block_size,
        )

        # Get the size of the file on disk.
        stat = os.stat(shard_path)
        return stat.st_size

    def get_shards(self, world: "World", allow_unsafe_types: bool) -> list["Reader"]:
        """Load this Stream's index, retrieving its shard readers.

        Args:
            world (World): Distributed context.
            allow_unsafe_types (bool): If a shard contains Pickle, which allows arbitrary code
                execution during deserialization, whether to keep going if ``True`` or raise an error.
                This argument is ignored as SpiralStream does not support Pickle.

        Returns:
            `List[Reader]: Shard readers.
        """
        basepath = os.path.join(self._cache_dir, self.split)
        return [SpiralReader(shard, basepath) for shard in self._shards]  # type: ignore[return-value]

    def set_up_local(self, shards: list["Reader"], cache_usage_per_shard: "NDArray[np.int64]") -> None:
        """Bring a local directory into a consistent state, getting which shards are present.

        Args:
            shards (List[Reader]): List of this stream's shards.
            cache_usage_per_shard (NDArray[np.int64]): Cache usage per shard of this stream.
        """
        listing = set()
        for file in os.listdir(os.path.join(self._cache_dir, self.split)):
            if os.path.isfile(os.path.join(self._cache_dir, self.split, file)) and file.endswith(".vortex"):
                listing.add(file)

        # Determine which shards are present, making local dir consistent.
        for i, shard in enumerate(shards):
            if not isinstance(shard, SpiralReader):
                raise ValueError("Only SpiralReader is supported in SpiralStream")
            if shard.filename in listing:
                # Get the size of the file on disk.
                stat = os.stat(os.path.join(self._cache_dir, self.split, shard.filename))
                cache_usage_per_shard[i] = stat.st_size
            else:
                cache_usage_per_shard[i] = 0

    def get_index_size(self) -> int:
        """Get the size of the index file in bytes.

        Returns:
            int: Size in bytes.
        """
        # There is no index file stored on disk.
        return 0
