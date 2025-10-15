import pyarrow as pa
from spiral.core.table import KeyRange
from spiral.core.table.spec import FileFormat, FragmentLevel, KeyExtent, KeySpan
from spiral.types_ import Timestamp

class FragmentManifest:
    def __len__(self): ...
    def __getitem__(self, idx: int): ...
    def to_arrow(self) -> pa.RecordBatchReader: ...
    @staticmethod
    def compute_schema() -> pa.Schema: ...
    @staticmethod
    def from_fragment(fragment_file: FragmentFile) -> FragmentManifest: ...
    @staticmethod
    def from_arrow(reader: pa.RecordBatchReader) -> FragmentManifest: ...
    @staticmethod
    def empty() -> FragmentManifest: ...

class FragmentFile:
    id: str
    committed_at: Timestamp | None
    compacted_at: Timestamp | None
    format: FileFormat
    format_metadata: bytes | None
    size_bytes: int
    column_ids: list[str]
    level: FragmentLevel
    # NOTE: Empty for key space files.
    column_ids: list[str]
    ks_id: str
    key_span: KeySpan
    key_extent: KeyExtent

    @property
    def key_range(self) -> KeyRange: ...
