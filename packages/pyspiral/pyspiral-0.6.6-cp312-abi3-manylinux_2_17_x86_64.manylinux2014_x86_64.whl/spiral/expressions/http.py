import hishel
import httpx
import pyarrow as pa

from spiral.expressions.base import Expr, ExprLike
from spiral.expressions.struct import pack
from spiral.expressions.udf import UDF
from spiral.settings import APP_DIR


def get(url: ExprLike, headers: ExprLike = None, force_cache: bool = False) -> Expr:
    """Submit a GET request to either a scalar of vector of URLs."""
    to_pack = {"url": url}
    if headers is not None:
        to_pack["headers"] = headers
    return HttpGet(force_cache)(pack(to_pack))


class HttpGet(UDF):
    RES_DTYPE: pa.DataType = pa.struct(
        [
            pa.field("bytes", pa.large_binary()),
            pa.field("status", pa.int32()),
            pa.field("headers", pa.map_(pa.string(), pa.string())),
        ]
    )

    def __init__(self, force_cache: bool = False):
        super().__init__("http.get")
        self._force_cache = force_cache

    def return_type(self, *input_types: pa.DataType) -> pa.DataType:
        return HttpGet.RES_DTYPE

    def invoke(self, *input_args: pa.Array) -> pa.Array:
        if len(input_args) != 1:
            raise ValueError(f"Expected 1 argument, got {len(input_args)}")
        result = _http_request(input_args[0], self._force_cache)
        if isinstance(result, pa.ChunkedArray):
            result = result.combine_chunks()
        return result


def _http_request(arg: pa.Array, force_cache: bool) -> pa.Array:
    client = _HttpClient()

    if isinstance(arg, pa.StructArray):
        # We assume a vector of requests, but with potentially many arguments
        return pa.array(
            [
                _response_dict(
                    client.request(
                        req.get("method", "GET").upper(),
                        req["url"],
                        headers=req.get("headers", {}),
                        extensions={"force_cache": force_cache},
                    )
                )
                for req in arg.to_pylist()
            ],
            type=HttpGet.RES_DTYPE,
        )

    raise TypeError(f"Unsupported argument: {arg} ({type(arg)})")


def _response_dict(response: httpx.Response) -> dict:
    if response.status_code != 200:
        raise ValueError(f"Request failed with status {response.status_code}")
    return {
        "bytes": response.read(),
        "status": response.status_code,
        "headers": dict(response.headers),
    }


class _HttpClient(hishel.CacheClient):
    _instance: "_HttpClient" = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__(storage=hishel.FileStorage(base_path=APP_DIR / "http.cache", ttl=3600))
