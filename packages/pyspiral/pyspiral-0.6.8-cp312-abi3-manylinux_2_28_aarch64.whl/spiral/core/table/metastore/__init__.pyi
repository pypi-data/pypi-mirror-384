"""The SpiralDB metastore API."""

from spiral.core.client import Authn
from spiral.core.table.spec import ColumnGroup, ColumnGroupMetadata, FileFormat, KeySpaceMetadata, Schema, WriteAheadLog
from spiral.types_ import Uri

class FileHandle:
    def __init__(self, *, uri: str, format: FileFormat, spfs_token: str | None): ...

    uri: str
    format: FileFormat
    spfs_token: str | None

class FileRef:
    def __init__(self, *, id: str, file_type: FileType, file_format: FileFormat): ...

    id: str
    file_type: FileType
    file_format: FileFormat

    def resolve_uri(self, root_uri: str) -> str:
        """Resolves the file reference URI given the root URI."""

class FileType:
    FragmentFile: FileType
    FragmentManifest: FileType
    ReferenceFile: FileType

    def __int__(self) -> int:
        """Returns the protobuf enum int value."""

class PyMetastore:
    """Rust implementation of the metastore API."""

    @property
    def table_id(self) -> str: ...
    @property
    def root_uri(self) -> Uri: ...
    @property
    def key_schema(self) -> Schema: ...
    def get_wal(self) -> WriteAheadLog:
        """Return the log for the table."""
    def get_key_space_metadata(self) -> KeySpaceMetadata:
        """Return the metadata for the key space."""
        ...
    def get_column_group_metadata(self, column_group: ColumnGroup) -> ColumnGroupMetadata:
        """Return the metadata for a column group."""
        ...

    @staticmethod
    def http(
        table_id: str,
        root_uri: str,
        key_schema: Schema,
        base_url: str,
        authn: Authn,
    ) -> PyMetastore:
        """Construct a PyMetastore backed by an HTTP metastore service."""
