from sqlalchemy.orm import DeclarativeBase
from typing import Any, Tuple, TypeVar


DeclarativeBaseT = TypeVar("DeclarativeBaseT", bound=DeclarativeBase)
RowT = TypeVar("RowT", bound=Tuple[Any, ...])
