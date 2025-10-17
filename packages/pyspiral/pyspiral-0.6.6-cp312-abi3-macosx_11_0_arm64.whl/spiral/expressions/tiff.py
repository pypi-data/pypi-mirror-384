import numpy as np
import pyarrow as pa

from spiral.expressions.base import Expr, ExprLike
from spiral.expressions.udf import RefUDF

_TIFF_RES_DTYPE: pa.DataType = pa.struct(
    [
        pa.field("pixels", pa.large_binary()),
        pa.field("height", pa.uint32()),
        pa.field("width", pa.uint32()),
        pa.field("channels", pa.uint8()),
        pa.field("channel_bit_depth", pa.uint8()),
    ]
)


def read(
    expr: ExprLike,
    indexes: ExprLike | int | None = None,
    window: ExprLike | tuple[tuple[int, int], tuple[int, int]] | None = None,
    boundless: ExprLike | bool | None = None,
) -> Expr:
    """
    Read referenced cell in a `TIFF` format. Requires `rasterio` to be installed.

    Args:
        expr: The referenced `TIFF` bytes.
        indexes: The band indexes to read. Defaults to all.
        window: The window to read. In format (row_range_tuple, col_range_tuple). Defaults to full window.
        boundless: If `True`, windows that extend beyond the dataset's extent
            are permitted and partially or completely filled arrays will be returned as appropriate.

    Returns:
        An array where each element is a decoded image with fields:
            pixels: bytes of shape (channels, width, height).
            width: Width of the image with type `pa.uint32()`.
            height: Height of the image with type `pa.uint32()`.
            channels: Number of channels of the image with type `pa.uint8()`.
                If `indexes` is not None, this is the length of `indexes` or 1 if `indexes` is an int.
            channel_bit_depth: Bit depth of the channel with type `pa.uint8()`.
    """
    try:
        import rasterio  # noqa: F401
    except ImportError:
        raise ImportError("`rasterio` is required for tiff.read")

    return TiffReadUDF()(expr, indexes, window, boundless)


def select(
    expr: ExprLike,
    shape: ExprLike | dict,
    indexes: ExprLike | int | None = None,
) -> Expr:
    """
    Select the shape out of the referenced cell in a `TIFF` format. Requires `rasterio` to be installed.

    Args:
        expr: The referenced `TIFF` bytes.
        shape: [GeoJSON-like](https://geojson.org/) shape.
        indexes: The band indexes to read. Defaults to all.

    Returns:
        An array where each element is a decoded image with fields:
            pixels: bytes of shape (len(indexes) or 1, width, height).
            width: Width of the image with type `pa.uint32()`.
            height: Height of the image with type `pa.uint32()`.
            channels: Number of channels of the image with type `pa.uint8()`.
                If `indexes` is not None, this is the length of `indexes` or 1 if `indexes` is an int.
            channel_bit_depth: Bit depth of the channel with type `pa.uint8()`.
    """
    try:
        import rasterio  # noqa: F401
    except ImportError:
        raise ImportError("`rasterio` is required for tiff.select")

    return TiffSelectUDF()(expr, shape, indexes)


class TiffReadUDF(RefUDF):
    def __init__(self):
        super().__init__("tiff.read")

    def return_type(self, *input_types: pa.DataType) -> pa.DataType:
        return _TIFF_RES_DTYPE

    def invoke(self, fp, *input_args: pa.Array) -> pa.Array:
        try:
            import rasterio
        except ImportError:
            raise ImportError("`rasterio` is required for tiff.read")

        from rasterio.windows import Window

        if len(input_args) != 4:
            raise ValueError("tiff.read expects exactly 4 arguments: expr, indexes, window, boundless")

        _, indexes, window, boundless = input_args

        indexes = indexes[0].as_py()
        if indexes is not None and not isinstance(indexes, int) and not isinstance(indexes, list):
            raise ValueError(f"tiff.read expects indexes to be None or an int or a list, got {indexes}")

        boundless = boundless[0].as_py()
        if boundless is not None and not isinstance(boundless, bool):
            raise ValueError(f"tiff.read expects boundless to be None or a bool, got {boundless}")

        window = window[0].as_py()
        if window is not None:
            if len(window) != 2:
                raise ValueError(f"tiff.read window invalid, got {window}")
            window = Window.from_slices(slice(*window[0]), slice(*window[1]), boundless=boundless or False)

        opener = _VsiOpener(fp)
        with rasterio.open("ref", opener=opener) as src:
            src: rasterio.DatasetReader
            # TODO(marko): We know the size and dtype so we should be able to preallocate the result and read into it.
            #   This matters more if we want to rewrite this function to work with multiple inputs at once, in which
            #   case we should first consider using Rust GDAL bindings - I believe rasterio uses GDAL under the hood.
            result: np.ndarray = src.read(indexes=indexes, window=window)
            return _return_result(result, indexes)


class TiffSelectUDF(RefUDF):
    def __init__(self):
        super().__init__("tiff.select")

    def return_type(self, *input_types: pa.DataType) -> pa.DataType:
        return _TIFF_RES_DTYPE

    def invoke(self, fp, *input_args: pa.Array) -> pa.Array:
        try:
            import rasterio
        except ImportError:
            raise ImportError("`rasterio` is required for tiff.select")

        from rasterio.mask import raster_geometry_mask

        if len(input_args) != 3:
            raise ValueError("tiff.select expects exactly 3 arguments: expr, shape, indexes")

        _, shape, indexes = input_args

        shape = shape[0].as_py()
        if shape is None:
            raise ValueError("tiff.select expects shape to be a GeoJSON-like shape")

        indexes = indexes[0].as_py()
        if indexes is not None and not isinstance(indexes, int) and not isinstance(indexes, list):
            raise ValueError(f"tiff.select expects indexes to be None or an int or a list, got {indexes}")

        opener = _VsiOpener(fp)
        with rasterio.open("ref", opener=opener) as src:
            src: rasterio.DatasetReader

            shape_mask, _, window = raster_geometry_mask(src, [shape], crop=True)
            out_shape = (src.count,) + shape_mask.shape

            result: np.ndarray = src.read(window=window, indexes=indexes, out_shape=out_shape, masked=True)
            return _return_result(result, indexes)


def _return_result(result: np.ndarray, indexes) -> pa.Array:
    channels = result.shape[0]
    if indexes is None:
        pass
    elif isinstance(indexes, int):
        assert channels == 1, f"Expected 1 channel, got {channels}"
    else:
        assert channels == len(indexes), f"Expected {len(indexes)} channels, got {channels}"

    if result.dtype == np.uint8:
        channel_bit_depth = 8
    elif result.dtype == np.uint16:
        channel_bit_depth = 16
    else:
        raise ValueError(f"Unsupported bit width: {result.dtype}")

    return pa.array(
        [
            {
                "pixels": result.tobytes(),
                "height": result.shape[1],
                "width": result.shape[2],
                "channels": channels,
                "channel_bit_depth": channel_bit_depth,
            }
        ],
        type=_TIFF_RES_DTYPE,
    )


class _VsiOpener:
    """
    VSI file opener which returns a constant file-like on open.

    Must match https://rasterio.readthedocs.io/en/stable/topics/vsi.html#python-file-and-filesystem-openers spec but
    only `open` is needed when going through rasterio.
    """

    def __init__(self, file_like):
        self._file_like = file_like

    def open(self, _path, mode):
        if mode not in {"r", "rb"}:
            raise ValueError(f"Unsupported mode: {mode}")
        return self._file_like

    def isdir(self, _):
        return False

    def isfile(self, _):
        return False

    def mtime(self, _):
        return 0

    def size(self, _):
        return self._file_like.size()

    def modified(self, _):
        raise NotImplementedError
