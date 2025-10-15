from ._bug import (
    LibraryBug,
)
from fa_purity import (
    Coproduct,
    CoproductFactory,
    FrozenList,
    Result,
    Unsafe,
)
from fa_purity.json import (
    JsonObj,
    JsonValueFactory,
    Unfolder,
)
from requests import (
    Response,
)
from requests.exceptions import (
    HTTPError,
    JSONDecodeError,
)


def handle_status(response: Response) -> Result[Response, HTTPError]:
    try:
        response.raise_for_status()
        return Result.success(response)
    except HTTPError as err:
        return Result.failure(err)


def json_decode(
    response: Response,
) -> Result[Coproduct[JsonObj, FrozenList[JsonObj]], JSONDecodeError]:
    try:
        _factory: CoproductFactory[JsonObj, FrozenList[JsonObj]] = CoproductFactory()
        raw = response.json()  # type: ignore[misc]
        result = JsonValueFactory.from_any(raw).bind(  # type: ignore[misc]
            lambda v: Unfolder.to_list_of(v, Unfolder.to_json)
            .map(_factory.inr)
            .lash(lambda _: Unfolder.to_json(v).map(_factory.inl))
            .alt(
                lambda e: ValueError(
                    f"Impossible. Decode error, not a json nor a list[json] i.e. {e}"
                )
            )
            .alt(LibraryBug)
        )
        return Result.success(
            result.alt(LibraryBug).alt(Unsafe.raise_exception).to_union()
        )
    except JSONDecodeError as err:
        return Result.failure(err)
