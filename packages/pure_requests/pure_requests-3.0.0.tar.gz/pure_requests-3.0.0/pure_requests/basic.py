from ._bug import (
    LibraryBug,
)
from dataclasses import (
    dataclass,
)
from enum import (
    Enum,
)
from fa_purity import (
    Cmd,
    Result,
)
from fa_purity.json import (
    JsonObj,
    JsonValue,
    Unfolder,
)
import requests
from requests import (
    Response,
)
from requests.auth import (
    HTTPBasicAuth,
    HTTPDigestAuth,
    HTTPProxyAuth,
)
from requests.exceptions import (
    RequestException,
)
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Union,
)


class AuthMethod(Enum):
    BASIC = "BASIC"
    DIGEST = "DIGEST"
    PROXY = "PROXY"


@dataclass(frozen=True)
class Authentication:
    user: Union[str, bytes]
    password: Union[str, bytes]
    method: AuthMethod

    def __repr__(self) -> str:
        return f"Authentication: method={self.method} user=? pass=?"


def _to_requests_obj(
    auth: Authentication,
) -> Union[HTTPBasicAuth, HTTPDigestAuth, HTTPProxyAuth]:
    if auth.method is AuthMethod.BASIC:
        return HTTPBasicAuth(auth.user, auth.password)
    if auth.method is AuthMethod.DIGEST:
        return HTTPDigestAuth(auth.user, auth.password)
    if auth.method is AuthMethod.PROXY:
        return HTTPProxyAuth(auth.user, auth.password)
    raise ValueError("Impossible")


def _to_raw_dict(item: JsonObj) -> Dict[str, Any]:  # type: ignore[explicit-any]
    result = Unfolder.to_raw(JsonValue.from_json(item))  # type: ignore[misc]
    if isinstance(result, dict):  # type: ignore[misc]
        return result
    raise LibraryBug(ValueError(f"Expected a `dict` but got {type(item)}"))


@dataclass(frozen=True)
class Endpoint:
    raw: str


@dataclass(frozen=True)
class Params:
    raw: JsonObj


@dataclass(frozen=True)
class Data:
    raw: Union[JsonObj, str]


@dataclass(frozen=True)
class HttpClient:
    get: Callable[[Endpoint, Params], Cmd[Result[Response, RequestException]]]
    post: Callable[[Endpoint, Params, Data], Cmd[Result[Response, RequestException]]]


@dataclass(frozen=True)
class _HttpClient1:
    _auth: Optional[Authentication]
    _headers: Optional[JsonObj]
    _stream: Optional[bool]

    def get(
        self,
        endpoint: Endpoint,
        params: Params,
    ) -> Cmd[Result[Response, RequestException]]:
        def _action() -> Result[Response, RequestException]:
            try:
                headers = (
                    _to_raw_dict(self._headers)  # type: ignore[misc]
                    if self._headers is not None
                    else None
                )
                result = requests.get(  # pylint: disable=missing-timeout
                    endpoint.raw,
                    headers=headers,  # type: ignore[misc]
                    params=_to_raw_dict(params.raw),  # type: ignore[misc]
                    auth=_to_requests_obj(self._auth)
                    if self._auth is not None
                    else None,
                    stream=self._stream,
                )
                return Result.success(result)
            except RequestException as err:
                return Result.failure(err)

        return Cmd.wrap_impure(_action)

    def post(
        self,
        endpoint: Endpoint,
        params: Params,
        data: Data,
    ) -> Cmd[Result[Response, RequestException]]:
        def _action() -> Result[Response, RequestException]:
            try:
                headers = (
                    _to_raw_dict(self._headers)  # type: ignore[misc]
                    if self._headers is not None
                    else None
                )
                json = (
                    _to_raw_dict(data.raw)  # type: ignore[misc]
                    if not isinstance(data.raw, str)
                    else None
                )
                response = requests.post(  # pylint: disable=missing-timeout
                    endpoint.raw,
                    headers=headers,  # type: ignore[misc]
                    params=_to_raw_dict(params.raw),  # type: ignore[misc]
                    json=json,  # type: ignore[misc]
                    data=data.raw if isinstance(data.raw, str) else None,
                    auth=_to_requests_obj(self._auth)
                    if self._auth is not None
                    else None,
                    stream=self._stream,
                )
                return Result.success(response)
            except RequestException as err:
                return Result.failure(err)

        return Cmd.wrap_impure(_action)


@dataclass(frozen=True)
class HttpClientFactory:
    @staticmethod
    def new_client(
        auth: Optional[Authentication],
        headers: Optional[JsonObj],
        stream: Optional[bool],
    ) -> HttpClient:
        client = _HttpClient1(auth, headers, stream)
        return HttpClient(client.get, client.post)
