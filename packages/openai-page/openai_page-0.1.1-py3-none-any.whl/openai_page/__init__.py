import pathlib
import typing

import pydantic

__version__ = pathlib.Path(__file__).parent.joinpath("VERSION").read_text().strip()

_T = typing.TypeVar("_T")


class Page(pydantic.BaseModel, typing.Generic[_T]):
    data: typing.List[_T]
    has_more: bool = pydantic.Field(default=False)
    object: typing.Literal["list"] = pydantic.Field(default="list")
    first_id: str | None = pydantic.Field(default=None)
    last_id: str | None = pydantic.Field(default=None)
