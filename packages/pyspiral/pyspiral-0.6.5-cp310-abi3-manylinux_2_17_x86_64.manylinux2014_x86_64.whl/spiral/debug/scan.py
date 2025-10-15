from datetime import datetime

from spiral.core.table import Scan
from spiral.core.table.manifests import FragmentFile, FragmentManifest
from spiral.core.table.spec import Key
from spiral.types_ import Timestamp


def show_scan(scan: Scan):
    """Displays a scan in a way that is useful for debugging."""
    table_ids = scan.table_ids()
    if len(table_ids) > 1:
        raise NotImplementedError("Multiple table scan is not supported.")
    table_id = table_ids[0]
    column_groups = scan.column_groups()

    splits = scan.splits()
    key_space_state = scan.key_space_state(table_id)

    # Collect all key bounds from all manifests. This makes sure all visualizations are aligned.
    key_points = set()
    key_space_manifest = key_space_state.manifest
    for i in range(len(key_space_manifest)):
        fragment_file = key_space_manifest[i]
        key_points.add(fragment_file.key_extent.min)
        key_points.add(fragment_file.key_extent.max)
    for cg in column_groups:
        cg_scan = scan.column_group_state(cg)
        cg_manifest = cg_scan.manifest
        for i in range(len(cg_manifest)):
            fragment_file = cg_manifest[i]
            key_points.add(fragment_file.key_extent.min)
            key_points.add(fragment_file.key_extent.max)

    # Make sure split points exist in all key points.
    for s in splits[:-1]:  # Don't take the last end.
        key_points.add(s.end)
    key_points = list(sorted(key_points))

    show_manifest(key_space_manifest, scope="Key space", key_points=key_points, splits=splits)
    for cg in scan.column_groups():
        cg_scan = scan.column_group_state(cg)
        # Skip table id from the start of the column group.
        show_manifest(cg_scan.manifest, scope=".".join(cg.path[1:]), key_points=key_points, splits=splits)


def show_manifest(manifest: FragmentManifest, scope: str = None, key_points: list[Key] = None, splits: list = None):
    try:
        import matplotlib.patches as patches
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for debug")

    total_fragments = len(manifest)

    size_points = set()
    for i in range(total_fragments):
        manifest_file: FragmentFile = manifest[i]
        size_points.add(manifest_file.size_bytes)
    size_points = list(sorted(size_points))

    if key_points is None:
        key_points = set()

        for i in range(total_fragments):
            manifest_file: FragmentFile = manifest[i]

            key_points.add(manifest_file.key_extent.min)
            key_points.add(manifest_file.key_extent.max)

        if splits is not None:
            for split in splits[:-1]:
                key_points.add(split.end)

        key_points = list(sorted(key_points))

    # Create figure and axis with specified size
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot each rectangle
    for i in range(total_fragments):
        manifest_file: FragmentFile = manifest[i]

        left = key_points.index(manifest_file.key_extent.min)
        right = key_points.index(manifest_file.key_extent.max)
        height = size_points.index(manifest_file.size_bytes) + 1

        color = _get_fragment_color(manifest_file, i, total_fragments)

        # Create rectangle patch
        rect = patches.Rectangle(
            (left, 0),  # (x, y)
            right - left,  # width
            height,  # height
            facecolor=color,  # fill color
            edgecolor="black",  # border color
            alpha=0.5,  # transparency
            linewidth=1,  # border width
            label=manifest_file.id,  # label for legend
        )

        ax.add_patch(rect)

    # Set axis limits with some padding
    ax.set_xlim(-0.5, len(key_points) - 1 + 0.5)
    ax.set_ylim(-0.5, len(size_points) + 0.5)

    # Create split markers on x-axis
    if splits is not None:
        split_positions = [key_points.index(split.end) for split in splits[:-1]]

        # Add split markers at the bottom
        for pos in split_positions:
            ax.annotate("▲", xy=(pos, 0), ha="center", va="top", color="red", annotation_clip=False)

    # Add grid
    ax.grid(True, linestyle="--", alpha=0.7, zorder=0)

    # Add labels and title
    ax.set_title("Fragment Distribution" if scope is None else f"{scope} Fragment Distribution")
    ax.set_xlabel("Key Index")
    ax.set_ylabel("Size Index")

    # Add legend
    ax.legend(bbox_to_anchor=(1, 1), loc="upper left", fontsize="small")

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    plot = FragmentManifestPlot(fig, ax, manifest)
    fig.canvas.mpl_connect("motion_notify_event", plot.hover)

    plt.show()


def _get_fragment_color(manifest_file: FragmentFile, color_index, total_colors):
    import matplotlib.cm as cm

    if manifest_file.compacted_at is not None:
        # Use a shade of gray for compacted fragments
        # Vary the shade based on the index to distinguish different compacted fragments
        gray_value = 0.3 + (0.5 * (color_index / total_colors))
        return (gray_value, gray_value, gray_value)
    else:
        # Use viridis colormap for non-compacted fragments
        return cm.viridis(color_index / total_colors)


def _get_human_size(size_bytes: int) -> str:
    # Convert bytes to a human-readable format
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def _maybe_truncate(text, max_length: int = 30) -> str:
    text = str(text)
    if len(text) <= max_length:
        return text

    half_length = (max_length - 3) // 2
    return text[:half_length] + "..." + text[-half_length:]


def _get_fragment_legend(manifest_file: FragmentFile):
    return "\n".join(
        [
            f"id: {manifest_file.id}",
            f"size: {_get_human_size(manifest_file.size_bytes)} ({manifest_file.size_bytes} bytes)",
            f"key_span: {manifest_file.key_span}",
            f"key_min: {_maybe_truncate(manifest_file.key_extent.min)}",
            f"key_max: {_maybe_truncate(manifest_file.key_extent.max)}",
            f"format: {manifest_file.format}",
            f"level: {manifest_file.level}",
            f"committed_at: {_format_timestamp(manifest_file.committed_at)}",
            f"compacted_at: {_format_timestamp(manifest_file.compacted_at)}",
            f"ks_id: {manifest_file.ks_id}",
        ]
    )


def _format_timestamp(ts: Timestamp | None) -> str:
    # Format timestamp or show None
    if ts is None:
        return "None"
    try:
        return datetime.fromtimestamp(ts / 1e6).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return str(ts)


class FragmentManifestPlot:
    def __init__(self, fig, ax, manifest: FragmentManifest):
        self.fig = fig
        self.ax = ax
        self.manifest = manifest

        # Position the annotation in the bottom right corner
        self.annotation = ax.annotate(
            "",
            xy=(0.98, 0.02),  # Position in axes coordinates
            xycoords="axes fraction",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8),
            ha="right",  # Right-align text
            va="bottom",  # Bottom-align text
            visible=False,
        )
        self.highlighted_rect = None
        self.highlighted_legend = None

    def hover(self, event):
        if event.inaxes != self.ax:
            # Check if we're hovering over the legend
            legend = self.ax.get_legend()
            if legend and legend.contains(event)[0]:
                # Find which legend item we're hovering over
                for i, legend_text in enumerate(legend.get_texts()):
                    if legend_text.contains(event)[0]:
                        manifest_file = self.manifest[i]
                        self._show_legend(manifest_file, i, legend_text)
                        return
            self._hide_legend()
            return

        # Check rectangles in the main plot
        for i, rect in enumerate(self.ax.patches):
            if rect.contains(event)[0]:
                manifest_file = self.manifest[i]
                self._show_legend(manifest_file, i, rect)
                return

        self._hide_legend()

    def _show_legend(self, manifest_file, index, highlight_obj):
        import matplotlib.patches as patches

        # Update tooltip text
        self.annotation.set_text(_get_fragment_legend(manifest_file))
        self.annotation.set_visible(True)

        # Handle highlighting
        if isinstance(highlight_obj, patches.Rectangle):
            # Highlighting rectangle in main plot
            if self.highlighted_rect and self.highlighted_rect != highlight_obj:
                self.highlighted_rect.set_alpha(0.5)
            highlight_obj.set_alpha(0.8)
            self.highlighted_rect = highlight_obj
        else:
            # Highlighting legend text
            if self.highlighted_rect:
                self.highlighted_rect.set_alpha(0.5)
            # Find and highlight corresponding rectangle
            rect = self.ax.patches[index]
            rect.set_alpha(0.8)
            self.highlighted_rect = rect

        self.fig.canvas.draw_idle()

    def _hide_legend(self):
        if self.annotation.get_visible():
            self.annotation.set_visible(False)
            if self.highlighted_rect:
                self.highlighted_rect.set_alpha(0.5)
            self.fig.canvas.draw_idle()
