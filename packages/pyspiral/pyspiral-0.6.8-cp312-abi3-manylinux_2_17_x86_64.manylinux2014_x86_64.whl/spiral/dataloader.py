from __future__ import annotations

import os
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from typing import Any

import pyarrow as pa

from spiral.core.client import Shard
from spiral.scan import Scan


@dataclass(frozen=True)
class World:
    """Distributed training configuration.
    Attributes:
        rank: Process rank (0 to world_size-1).
        world_size: Total number of processes.
    """

    rank: int
    world_size: int

    def shards(
        self,
        shards: list[Shard],
        shuffle_seed: int | None = None,
    ) -> list[Shard]:
        """Partition shards for distributed training.

        Args:
            shards: List of Shard objects to partition.
            shuffle_seed: Optional seed to shuffle before partitioning.

        Returns:
            Subset of shards for this rank (round-robin partitioning).
        """
        if shuffle_seed is not None:
            shards = World._shuffle(shards, shuffle_seed)

        return shards[self.rank :: self.world_size]

    @classmethod
    def from_torch(cls) -> World:
        """Auto-detect world configuration from PyTorch distributed."""
        try:
            import torch.distributed as dist

            if dist.is_available() and dist.is_initialized():
                return cls(
                    rank=dist.get_rank(),
                    world_size=dist.get_world_size(),
                )
        except ImportError:
            pass

        return cls(
            rank=int(os.environ.get("RANK", 0)),
            world_size=int(os.environ.get("WORLD_SIZE", 1)),
        )

    @classmethod
    def _shuffle(cls, shards: list[Shard], seed: int) -> list[Shard]:
        """Shuffle shards deterministically with given seed."""
        shuffled = list(shards)
        random.Random(seed).shuffle(shuffled)
        return shuffled


# Top level so we can pickle this function
def _len_and_transform(batch: pa.RecordBatch, transform_fn: Callable) -> tuple[int, Any]:
    return (len(batch), transform_fn(batch))


class SpiralDataLoader:
    """DataLoader optimized for Spiral's multi-threaded streaming architecture.

    Unlike PyTorch's DataLoader which uses multiprocessing for I/O (num_workers),
    SpiralDataLoader leverages Spiral's efficient Rust-based streaming and only
    uses multiprocessing for CPU-bound post-processing transforms.

    Key differences from PyTorch DataLoader:
    - No num_workers for I/O (Spiral's Rust layer is already multi-threaded)
    - map_workers for parallel post-processing (tokenization, decoding, etc.)
    - Built-in checkpoint support via skip_samples
    - Explicit shard-based architecture for distributed training
    """

    # Example usage:
    #
    # Simple usage:
    #   loader = SpiralDataLoader(scan, batch_size=32)
    #   for batch in loader:
    #       train_step(batch)
    #
    # With parallel transforms:
    #   loader = SpiralDataLoader(
    #       scan,
    #       batch_size=32,
    #       transform_fn=tokenize_batch,
    #       map_workers=4,
    #   )

    def __init__(
        self,
        scan: Scan,
        *,
        shards: list[Shard] | None = None,
        shuffle_shards: bool = True,
        seed: int = 42,
        skip_samples: int = 0,
        shuffle_buffer_size: int = 0,
        batch_size: int = 32,
        batch_readahead: int | None = None,
        # TODO(os): accept vortex arrays here instead of Arrow
        transform_fn: Callable[[pa.RecordBatch], Any] | None = None,
        map_workers: int = 0,
    ):
        """Initialize SpiralDataLoader.

        Args:
            scan: Spiral scan to load data from.
            shards: Optional list of Shard objects to read. If None, uses
                scan's natural sharding based on physical layout.
            shuffle_shards: Whether to shuffle the list of shards.
                Uses the provided seed.
            seed: Base random seed for deterministic shuffling and checkpointing.
            skip_samples: Number of samples to skip at the beginning (for resuming
                from checkpoint).
            shuffle_buffer_size: Size of shuffle buffer for within-shard shuffling.
                0 means no shuffling.
            batch_size: Number of rows per batch.
            batch_readahead: Number of batches to prefetch in background. If None,
                uses a sensible default based on whether transforms are applied.
            transform_fn: Optional function to transform each batch. Takes a PyArrow
                RecordBatch and returns any type. Users can call batch.to_pydict()
                inside the function if they need a dict. If map_workers > 0, this
                function must be picklable.
            map_workers: Number of worker processes for parallel transform_fn
                application. 0 means single-process (no parallelism). Use this for
                CPU-bound transforms like tokenization or audio decoding.
        """
        self.scan = scan
        self.shards = shards if shards is not None else scan.shards()
        if shuffle_shards:
            self.shards = World._shuffle(self.shards, seed)
        self.seed = seed
        self.skip_samples = skip_samples
        self.shuffle_buffer_size = shuffle_buffer_size
        self.batch_size = batch_size
        self.batch_readahead = batch_readahead
        self.transform_fn = transform_fn
        self.map_workers = map_workers

        self._samples_yielded = 0

    def __iter__(self) -> Iterator[Any]:
        """Iterate over batches."""
        from spiral.core.client import ShuffleConfig

        shuffle = None
        if self.shuffle_buffer_size > 0:
            shuffle = ShuffleConfig(
                buffer_size=self.shuffle_buffer_size,
                seed=self.seed,
            )

        stream = self.scan.core.to_shuffled_record_batches(
            shards=self.shards,
            shuffle=shuffle,
            max_batch_size=self.batch_size,
            batch_readahead=self.batch_readahead,
            infinite=False,
        )

        if self.skip_samples > 0:

            def skip(s: Iterator[pa.RecordBatch], skip_count: int) -> Iterator[pa.RecordBatch]:
                """Skip samples from stream, yielding remaining batches."""
                skipped = 0
                for batch in s:
                    batch_size = len(batch)
                    if skipped + batch_size <= skip_count:
                        # Skip entire batch
                        skipped += batch_size
                        continue
                    elif skipped < skip_count:
                        # Partial skip - discard first N samples, yield remainder
                        skip_in_batch = skip_count - skipped
                        skipped = skip_count
                        yield batch[skip_in_batch:]
                    else:
                        # take the entire batch
                        yield batch

            stream = skip(stream, self.skip_samples)

        if self.transform_fn is None:
            for batch in stream:
                self._samples_yielded += len(batch)
                yield batch
        elif self.map_workers == 0:
            # Single-process transform
            for batch in stream:
                result = self.transform_fn(batch)
                self._samples_yielded += len(batch)
                yield result
        else:
            with Pool(self.map_workers) as pool:
                for batch_len, result in pool.imap(partial(_len_and_transform, transform_fn=self.transform_fn), stream):
                    self._samples_yielded += batch_len
                    yield result

    def state_dict(self) -> dict[str, Any]:
        """Get checkpoint state for resuming.

        Returns:
            Dictionary containing samples_yielded, seed, and shards.
        """
        # Example usage:
        #   loader = SpiralDataLoader(scan, batch_size=32, seed=42)
        #   for i, batch in enumerate(loader):
        #       if i == 10:
        #           checkpoint = loader.state_dict()
        #           break
        #
        #   # Resume later with exact same shards
        #   loader = SpiralDataLoader.from_state_dict(scan, checkpoint, batch_size=32)
        return {
            "samples_yielded": self._samples_yielded,
            "seed": self.seed,
            "shards": self.shards,  # Will be pickled automatically
        }

    @classmethod
    def from_state_dict(
        cls,
        scan: Scan,
        state: dict[str, Any],
        **kwargs,
    ) -> SpiralDataLoader:
        """Create a DataLoader from checkpoint state, resuming from where it left off.

        This is the recommended way to resume training from a checkpoint. It extracts
        the seed, samples_yielded, and shards from the state dict and creates a new
        DataLoader that will skip the already-processed samples.

        Args:
            scan: Spiral scan to load data from.
            state: Checkpoint state from state_dict().
            **kwargs: Additional arguments to pass to SpiralDataLoader constructor.
                These will override values in the state dict where applicable.

        Returns:
            New SpiralDataLoader instance configured to resume from the checkpoint.
        """
        # Example usage:
        #
        # Save checkpoint during training:
        #   loader = scan.to_distributed_data_loader(scan, batch_size=32, seed=42)
        #   checkpoint = loader.state_dict()
        #
        # Resume later using the same shards from checkpoint:
        #   resumed_loader = SpiralDataLoader.from_state_dict(
        #       scan,
        #       checkpoint,
        #       batch_size=32,
        #       transform_fn=my_transform,
        #   )

        # Extract resume parameters from state
        seed = state.get("seed", 42)
        skip_samples = state.get("samples_yielded", 0)
        shards = state.get("shards")

        # Allow kwargs to override state dict values
        seed = kwargs.pop("seed", seed)
        skip_samples = kwargs.pop("skip_samples", skip_samples)
        shards = kwargs.pop("shards", shards)

        return cls(scan, seed=seed, skip_samples=skip_samples, shards=shards, **kwargs)
