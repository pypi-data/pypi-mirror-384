"""Type definitions for the spiral.core.spec module shipped as part of the native library."""

import pyarrow as pa

class ColumnGroup:
    def __init__(self, path: list[str]): ...
    @property
    def table_id(self) -> str: ...
    @property
    def path(self) -> list[str]: ...
    def identifier(self, salt: int) -> str:
        """Return the column group identifier based on the given salt."""

    @staticmethod
    def from_str(path: str) -> ColumnGroup: ...

class KeySpaceMetadata:
    def __init__(
        self,
        *,
        manifest_handle: ManifestHandle | None,
        last_modified_at: int,
    ): ...

    manifest_handle: ManifestHandle | None
    last_modified_at: int

    def asof(self, asof: int) -> KeySpaceMetadata:
        """Returns the metadata as of a given timestamp. Currently just filtering versioned schemas."""
        ...

    def apply_wal(self, wal: WriteAheadLog) -> KeySpaceMetadata:
        """Applies the given WAL to the metadata."""

class ColumnGroupMetadata:
    def __init__(
        self,
        *,
        column_group: ColumnGroup,
        manifest_handle: ManifestHandle | None,
        last_modified_at: int,
        schema_versions: list[VersionedSchema] | None,
        immutable_schema: bool,
        schema_salt: int,
    ): ...

    column_group: ColumnGroup
    manifest_handle: ManifestHandle | None
    last_modified_at: int
    schema_versions: list[VersionedSchema]
    immutable_schema: bool
    schema_salt: int

    def latest_schema(self) -> VersionedSchema:
        """Returns the latest schema of the column group."""
        ...

    def asof(self, asof: int) -> ColumnGroupMetadata:
        """Returns the metadata as of a given timestamp. Currently just filtering versioned schemas."""
        ...

    def apply_wal(self, wal: WriteAheadLog) -> ColumnGroupMetadata:
        """Applies the given WAL to the metadata."""

class LogEntry:
    ts: int
    operation: (
        KeySpaceWriteOp
        | ColumnGroupWriteOp
        | SchemaEvolutionOp
        | SchemaBreakOp
        | KeySpaceCompactOp
        | ColumnGroupCompactOp
    )

    def column_group(self) -> ColumnGroup | None:
        """Returns the column group of the entry if it is associated with one."""

class FileFormat:
    def __init__(self, value: int): ...

    Parquet: FileFormat
    Protobuf: FileFormat
    BinaryArray: FileFormat
    Vortex: FileFormat

    def __int__(self) -> int:
        """Returns the protobuf enum int value."""
        ...

    def __str__(self) -> str:
        """Returns the string representation of the file format."""
        ...

class FragmentLevel:
    L0: FragmentLevel
    L1: FragmentLevel

    def __int__(self) -> int:
        """Returns the protobuf enum int value."""
        ...

class Key:
    def __init__(self, key: bytes): ...
    def __bytes__(self): ...
    def step(self) -> Key:
        """Returns the next key in the key space."""

    @staticmethod
    def min() -> Key: ...
    @staticmethod
    def max() -> Key: ...

class KeyExtent:
    """An inclusive range of keys."""

    def __init__(self, *, min: Key, max: Key): ...

    min: Key
    max: Key

    def union(self, key_extent: KeyExtent) -> KeyExtent: ...
    def __or__(self, other: KeyExtent) -> KeyExtent: ...
    def intersection(self, key_extent: KeyExtent) -> KeyExtent | None: ...
    def __and__(self, other: KeyExtent) -> KeyExtent | None: ...
    def contains(self, item: Key) -> bool: ...
    def __contains__(self, item: Key) -> bool: ...

class KeySpan:
    """An exclusive range of keys as indexed by their position in a key space."""

    def __init__(self, *, begin: int, end: int): ...

    begin: int
    end: int

    def __len__(self) -> int: ...
    def shift(self, offset: int) -> KeySpan: ...
    def union(self, other: KeySpan) -> KeySpan: ...
    def __or__(self, other: KeySpan) -> KeySpan: ...

class ManifestHandle:
    id: str
    format: FileFormat
    file_size: int

class Schema:
    def to_arrow(self) -> pa.Schema:
        """Returns the Arrow schema."""
        ...
    @staticmethod
    def from_arrow(arrow: pa.Schema) -> Schema:
        """Creates a Schema from an Arrow schema."""
        ...
    def __len__(self):
        """Returns the number of columns in the schema."""
        ...
    @property
    def names(self) -> list[str]:
        """Returns the names of the columns in the schema."""
        ...

class VersionedSchema:
    ts: int
    schema: Schema
    column_ids: list[str]

class KeySpaceWriteOp:
    ks_id: str
    manifest_handle: ManifestHandle

class ColumnGroupWriteOp:
    column_group: ColumnGroup
    level: FragmentLevel
    manifest_handle: ManifestHandle
    key_span: KeySpan
    key_extent: KeyExtent
    column_ids: list[str]

class SchemaEvolutionOp:
    column_group: ColumnGroup

class SchemaBreakOp:
    column_group: ColumnGroup

class KeySpaceCompactOp:
    ks_ids: list[str]
    moved_ks_ids: list[str]

class ColumnGroupCompactOp:
    column_group: ColumnGroup
    fragment_ids: list[int]

class WriteAheadLog:
    def __init__(
        self,
        *,
        entries: list[LogEntry] | None = None,
        truncated_up_to: int = 0,
    ): ...

    entries: list[LogEntry]
    truncated_up_to: int

    @property
    def last_modified_at(self) -> int:
        """Returns the timestamp of the last modification of the log."""

    def filter(
        self, asof: int | None = None, since: int | None = None, column_group: ColumnGroup | None = None
    ) -> WriteAheadLog:
        """Filters the WAL to entries by the given parameters."""
