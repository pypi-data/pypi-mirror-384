from typing import Any


def display_metrics(metrics: dict[str, Any]) -> None:
    """Display metrics in a formatted table."""
    print(
        f"{'Metric':<40} {'Type':<10} {'Count':<8} {'Avg':<12} {'Min':<12} "
        f"{'Max':<12} {'P95':<12} {'P99':<12} {'StdDev':<12}"
    )
    print("=" * 140)

    for metric_name, data in sorted(metrics.items()):
        metric_type = data["type"]
        count = data["count"]
        avg = _format_value(data["avg"], metric_type, metric_name)
        min_val = _format_value(data["min"], metric_type, metric_name)
        max_val = _format_value(data["max"], metric_type, metric_name)
        p95 = _format_value(data["p95"], metric_type, metric_name)
        p99 = _format_value(data["p99"], metric_type, metric_name)
        stddev = _format_value(data["stddev"], metric_type, metric_name)

        print(
            f"{metric_name:<40} {metric_type:<10} {count:<8} {avg:<12} {min_val:<12} "
            f"{max_val:<12} {p95:<12} {p99:<12} {stddev:<12}"
        )


def _format_duration(nanoseconds: float) -> str:
    """Convert nanoseconds to human-readable duration."""
    if nanoseconds >= 1_000_000_000:
        return f"{nanoseconds / 1_000_000_000:.2f}s"
    elif nanoseconds >= 1_000_000:
        return f"{nanoseconds / 1_000_000:.2f}ms"
    elif nanoseconds >= 1_000:
        return f"{nanoseconds / 1_000:.2f}μs"
    else:
        return f"{nanoseconds:.0f}ns"


def _format_bytes(bytes_value: float) -> str:
    """Convert bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f}TB"


def _format_value(value: float, metric_type: str, metric_name: str) -> str:
    """Format a value based on metric type and name."""
    if metric_type == "timer" or "duration" in metric_name:
        return _format_duration(value)
    elif "bytes" in metric_name:
        return _format_bytes(value)
    else:
        return f"{value:,.0f}"
