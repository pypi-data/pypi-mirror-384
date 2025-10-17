import tarfile
from io import BytesIO

import pyarrow as pa

from spiral.expressions.base import Expr, ExprLike
from spiral.expressions.struct import pack
from spiral.expressions.udf import UDF


def read_file(path: ExprLike) -> Expr:
    """
    Read file path(s) from disk into a struct with a single field "bytes" containing the file contents.

    Args:
        path: Expression evaluating to an array of strings representing local disk paths.
    """
    to_pack = {"path": path}
    return FileRead()(pack(to_pack))


class FileRead(UDF):
    RES_DTYPE: pa.DataType = pa.struct(
        [
            pa.field("bytes", pa.large_binary()),
        ]
    )

    def __init__(self):
        super().__init__("file.read")

    def return_type(self, *input_types: pa.DataType) -> pa.DataType:
        return FileRead.RES_DTYPE

    def invoke(self, *input_args: pa.Array) -> pa.Array:
        if len(input_args) != 1:
            raise ValueError(f"Expected 1 argument, got {len(input_args)}")
        arg = input_args[0]

        res = []
        for req in arg:
            with open(req["path"].as_py(), "rb") as f:
                res.append({"bytes": f.read()})

        return pa.array(res, type=FileRead.RES_DTYPE)


def read_tar(path: ExprLike = None, bytes_: ExprLike = None) -> "Expr":
    # Untar a vector of paths / byte arrays representing tarballs.
    if path is None and bytes_ is None:
        raise ValueError("Expected either path or bytes_ to be provided")
    to_pack = {}
    if path is not None:
        to_pack["path"] = path
    if bytes_ is not None:
        to_pack["bytes"] = bytes_
    return TarRead()(pack(to_pack))


class TarRead(UDF):
    RES_DTYPE = pa.list_(
        pa.struct(
            [
                pa.field("name", pa.string()),
                pa.field("bytes", pa.large_binary()),
            ]
        )
    )

    def __init__(self):
        super().__init__("tar.read")

    def return_type(self, *input_types: pa.DataType) -> pa.DataType:
        return TarRead.RES_DTYPE

    def invoke(self, *input_args: pa.Array) -> pa.Array:
        if len(input_args) != 1:
            raise ValueError(f"Expected 1 argument, got {len(input_args)}")
        arg = input_args[0]

        res = []
        for req in arg:
            if "path" in req:
                kwargs = {"name": req["path"].as_py()}
            elif "bytes" in req:
                kwargs = {"fileobj": BytesIO(req["bytes"].as_py())}
            else:
                raise ValueError("Expected path or bytes_ to be provided")

            files = []
            with tarfile.open(**kwargs) as f:
                for m in f.getmembers():
                    m: tarfile.TarInfo
                    if m.type == tarfile.DIRTYPE:
                        continue
                    # TODO(ngates): skip other types too maybe? Why are we even skipping directories?
                    files.append({"name": m.name, "bytes": f.extractfile(m).read()})
            res.append(files)

        return pa.array(res, type=TarRead.RES_DTYPE)
