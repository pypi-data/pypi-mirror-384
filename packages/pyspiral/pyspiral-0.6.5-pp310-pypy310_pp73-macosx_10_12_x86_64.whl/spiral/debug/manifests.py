from rich.console import Console
from rich.table import Table

from spiral import datetime_
from spiral.core.table import Scan
from spiral.core.table.manifests import FragmentManifest
from spiral.core.table.spec import ColumnGroup
from spiral.debug.metrics import _format_bytes


def display_scan_manifests(scan: Scan):
    """Display all manifests in a scan."""
    if len(scan.table_ids()) != 1:
        raise NotImplementedError("Multiple table scans are not supported.")
    table_id = scan.table_ids()[0]
    key_space_manifest = scan.key_space_state(table_id).manifest
    column_group_manifests = [
        (column_group, scan.column_group_state(column_group).manifest) for column_group in scan.column_groups()
    ]

    display_manifests(key_space_manifest, column_group_manifests)


def display_manifests(
    key_space_manifest: FragmentManifest, column_group_manifests: list[tuple[ColumnGroup, FragmentManifest]]
):
    _table_of_fragments(
        key_space_manifest,
        title="Key Space manifest",
    )

    for column_group, column_group_manifest in column_group_manifests:
        _table_of_fragments(
            column_group_manifest,
            title=f"Column Group manifest for {str(column_group)}",
        )


def _table_of_fragments(manifest: FragmentManifest, title: str):
    """Display fragments in a formatted table."""
    # Calculate summary statistics
    total_size = sum(fragment.size_bytes for fragment in manifest)
    total_metadata_size = sum(len(fragment.format_metadata or b"") for fragment in manifest)
    fragment_count = len(manifest)
    avg_size = total_size / fragment_count if fragment_count > 0 else 0

    # Print title and summary
    console = Console()
    console.print(f"\n\n{title}")
    console.print(
        f"{fragment_count} fragments, "
        f"total: {_format_bytes(total_size)}, "
        f"avg: {_format_bytes(int(avg_size))}, "
        f"metadata: {_format_bytes(total_metadata_size)}"
    )

    # Create rich table
    table = Table(title=None, show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Size (Metadata)", justify="right")
    table.add_column("Format", justify="center")
    table.add_column("Key Span", justify="center")
    table.add_column("Level", justify="center")
    table.add_column("Committed At", justify="center")
    table.add_column("Compacted At", justify="center")

    # Add each fragment as a row
    for fragment in manifest:
        committed_str = str(datetime_.from_timestamp_micros(fragment.committed_at)) if fragment.committed_at else "N/A"
        compacted_str = str(datetime_.from_timestamp_micros(fragment.compacted_at)) if fragment.compacted_at else "N/A"

        size_with_metadata = (
            f"{_format_bytes(fragment.size_bytes)} ({_format_bytes(len(fragment.format_metadata or b''))})"
        )
        key_span = f"{fragment.key_span.begin}..{fragment.key_span.end}"

        table.add_row(
            fragment.id,
            size_with_metadata,
            str(fragment.format),
            key_span,
            str(fragment.level),
            committed_str,
            compacted_str,
        )

    console.print(table)
