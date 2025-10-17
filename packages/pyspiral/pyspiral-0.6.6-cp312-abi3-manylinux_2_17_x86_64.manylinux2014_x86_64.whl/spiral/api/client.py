import logging
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, TypeVar

import httpx
from httpx import HTTPStatusError
from pydantic import BaseModel, Field, TypeAdapter

from spiral.core.authn import Authn

log = logging.getLogger(__name__)


E = TypeVar("E")


class PagedRequest(BaseModel):
    page_token: str | None = None
    page_size: int = 50


class PagedResponse[E](BaseModel):
    items: list[E] = Field(default_factory=list)
    next_page_token: str | None = None


PagedReqT = TypeVar("PagedReqT", bound=PagedRequest)


class Paged[E](Iterable[E]):
    def __init__(
        self,
        client: "_Client",
        path: str,
        page_token: str | None,
        page_size: int,
        response_cls: type[PagedResponse[E]],
        params: Mapping[str, str] | None = None,
    ):
        self._client = client
        self._path = path
        self._response_cls = response_cls

        self._page_size = page_size

        self._params = params or {}
        if page_token is not None:
            self._params["page_token"] = str(page_token)
        # TODO(marko): Support paging.
        # if page_size is not None:
        #     self._params["page_size"] = str(page_size)

        self._response: PagedResponse[E] = client.get(path, response_cls, params=self._params)

    @property
    def page(self) -> PagedResponse[E]:
        return self._response

    def __iter__(self) -> Iterator[E]:
        while True:
            yield from self._response.items

            if self._response.next_page_token is None:
                break

            params = self._params.copy()
            params["page_token"] = self._response.next_page_token
            self._response = self._client.get(self._path, self._response_cls, params=params)


class ServiceBase:
    def __init__(self, client: "_Client"):
        self.client = client


class SpiralHTTPError(Exception):
    def __init__(self, body: str, code: int):
        super().__init__(body)
        self.body = body
        self.code = code


class _Client:
    RequestT = TypeVar("RequestT")
    ResponseT = TypeVar("ResponseT")

    def __init__(self, http: httpx.Client, authn: Authn):
        self.http = http
        self.authn = authn

    def get(
        self, path: str, response_cls: type[ResponseT], *, params: Mapping[str, str | list[str]] | None = None
    ) -> ResponseT:
        return self.request("GET", path, None, response_cls, params=params)

    def post(
        self,
        path: str,
        req: RequestT,
        response_cls: type[ResponseT],
        *,
        params: Mapping[str, str | list[str]] | None = None,
    ) -> ResponseT:
        return self.request("POST", path, req, response_cls, params=params)

    def put(
        self,
        path: str,
        req: RequestT,
        response_cls: type[ResponseT],
        *,
        params: Mapping[str, str | list[str]] | None = None,
    ) -> ResponseT:
        return self.request("PUT", path, req, response_cls, params=params)

    def delete(
        self, path: str, response_cls: type[ResponseT], *, params: Mapping[str, str | list[str]] | None = None
    ) -> ResponseT:
        return self.request("DELETE", path, None, response_cls, params=params)

    def request(
        self,
        method: str,
        path: str,
        req: RequestT | None,
        response_cls: type[ResponseT],
        *,
        params: Mapping[str, str | list[str]] | None = None,
    ) -> ResponseT:
        req_data: dict[str, Any] = {}
        if req is not None:
            req_data = dict(json=TypeAdapter(req.__class__).dump_python(req, mode="json", exclude_none=True))

        token = self.authn.token()
        resp = self.http.request(
            method,
            path,
            params=params or {},
            headers={"authorization": f"Bearer {token.expose_secret()}"} if token else None,
            **req_data,
        )

        try:
            resp.raise_for_status()
        except HTTPStatusError as e:
            # Enrich the exception with the response body
            raise SpiralHTTPError(body=resp.text, code=resp.status_code) from e

        if response_cls == type[None]:
            assert resp.text == ""
            return None

        return TypeAdapter(response_cls).validate_python(resp.json())

    def paged(
        self,
        path: str,
        response_cls: type[PagedResponse[E]],
        *,
        page_token: str | None = None,
        page_size: int = 50,
        params: Mapping[str, str] | None = None,
    ) -> Paged[E]:
        return Paged(self, path, page_token, page_size, response_cls, params)
