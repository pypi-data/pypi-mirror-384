from typing import Annotated, TypeAlias

from pydantic import UrlConstraints

Uri: TypeAlias = Annotated[str, UrlConstraints()]
Timestamp: TypeAlias = int
