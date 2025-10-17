import pyarrow as pa

from spiral.expressions.base import Expr, ExprLike

_MP4_RES_DTYPE: pa.DataType = pa.struct(
    [
        pa.field("pixels", pa.large_binary()),
        pa.field("height", pa.uint32()),
        pa.field("width", pa.uint32()),
        pa.field("frames", pa.uint32()),
    ]
)


# TODO(marko): Support optional range and crop.
#   IMPORTANT: Frames is currently broken and defaults to full.
def read(expr: ExprLike | str, frames: ExprLike | str, crop: ExprLike | str):
    """
    Read referenced cell in a `MP4` format. Requires `ffmpeg`.

    Args:
        expr: The referenced `Mp4` bytes.
            A str is assumed to be the `se.aux` expression.
        frames: The range of frames to read. Each element must be a list of two uint32,
            frame start and frame end, or null / empty list to read all frames.
            A str is assumed to be the `se.aux` expression.
        crop: The crop of the frames to read. Each element must be a list of four uint32,
            x, y, width, height or null / empty list to read full frames.
            A str is assumed to be the `se.aux` expression.

    Returns:
        An array where each element is a decoded cropped video with fields:
            pixels: RGB8 bytes, frames * width * height * 3.
            width: Width of the image with type `pa.uint32()`.
            height: Height of the image with type `pa.uint32()`.
            frames: Number of frames with type `pa.uint32()`.
    """
    from spiral import _lib
    from spiral.expressions import aux, lift

    if isinstance(expr, str):
        expr = aux(
            expr,
            pa.struct([("__ref__", pa.struct([("id", pa.string()), ("begin", pa.uint64()), ("end", pa.uint64())]))]),
        )
    if isinstance(frames, str):
        frames = aux(frames, pa.list_(pa.uint32()))
    if isinstance(crop, str):
        crop = aux(crop, pa.list_(pa.uint32()))

    expr = lift(expr)
    frames = lift(frames)
    crop = lift(crop)

    return Expr(
        _lib.expr.video.read(
            expr.__expr__,
            frames.__expr__,
            crop.__expr__,
            format="mp4",
        )
    )
