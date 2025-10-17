from sqlalchemy import asc, cast, desc, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select
from sqlalchemy.types import DATE, String, TEXT, TIMESTAMP
from typing import Any, Sequence, Type
from maleo.enums.order import Order
from maleo.enums.status import OptListOfDataStatuses
from maleo.schemas.mixins.filter import DateFilter
from maleo.schemas.mixins.sort import SortColumn
from maleo.types.boolean import OptBool
from maleo.types.integer import OptListOfInts
from maleo.types.string import OptListOfStrs, OptStr
from .types import DeclarativeBaseT, RowT


def filter_column(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    column: str,
    value: Any = None,
    include_null: bool = False,
) -> Select[RowT]:
    column_attr = getattr(table, column, None)
    if column_attr is None or not isinstance(column_attr, InstrumentedAttribute):
        return stmt

    value_filters = []
    if value is not None:
        value_filters.extend([column_attr == val for val in value])

    if value_filters:
        if include_null:
            value_filters.append(column_attr.is_(None))
        stmt = stmt.filter(or_(*value_filters))

    return stmt


def filter_ids(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    column: str,
    ids: OptListOfInts = None,
    include_null: bool = False,
) -> Select[RowT]:
    column_attr = getattr(table, column, None)
    if column_attr is None or not isinstance(column_attr, InstrumentedAttribute):
        return stmt

    id_filters = []
    if ids is not None:
        id_filters.extend([column_attr == id for id in ids])

    if id_filters:
        if include_null:
            id_filters.append(column_attr.is_(None))
        stmt = stmt.filter(or_(*id_filters))

    return stmt


def filter_timestamps(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    date_filters: Sequence[DateFilter],
) -> Select[RowT]:
    if date_filters:
        for date_filter in date_filters:
            try:
                sqla_table = table.__table__
                column = sqla_table.columns[date_filter.name]
                column_attr: InstrumentedAttribute = getattr(table, date_filter.name)
                if isinstance(column.type, (TIMESTAMP, DATE)):
                    if date_filter.from_date and date_filter.to_date:
                        stmt = stmt.filter(
                            column_attr.between(
                                date_filter.from_date, date_filter.to_date
                            )
                        )
                    elif date_filter.from_date:
                        stmt = stmt.filter(column_attr >= date_filter.from_date)
                    elif date_filter.to_date:
                        stmt = stmt.filter(column_attr <= date_filter.to_date)
            except KeyError:
                continue
    return stmt


def filter_statuses(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    statuses: OptListOfDataStatuses,
) -> Select[RowT]:
    if statuses is not None:
        status_filters = [table.status == status for status in statuses]  # type: ignore
        stmt = stmt.filter(or_(*status_filters))
    return stmt


def filter_is_root(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    parent_column: str = "parent_id",
    is_root: OptBool = None,
) -> Select[RowT]:
    parent_attr = getattr(table, parent_column, None)
    if parent_attr is None or not isinstance(parent_attr, InstrumentedAttribute):
        return stmt
    if is_root is not None:
        stmt = stmt.filter(
            parent_attr.is_(None) if is_root else parent_attr.is_not(None)
        )
    return stmt


def filter_is_parent(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    id_column: str = "id",
    parent_column: str = "parent_id",
    is_parent: OptBool = None,
) -> Select[RowT]:
    id_attr = getattr(table, id_column, None)
    if id_attr is None or not isinstance(id_attr, InstrumentedAttribute):
        return stmt
    parent_attr = getattr(table, parent_column, None)
    if parent_attr is None or not isinstance(parent_attr, InstrumentedAttribute):
        return stmt
    if is_parent is not None:
        child_table = aliased(table)
        child_parent_attr = getattr(child_table, parent_column)
        subq = select(child_table).filter(child_parent_attr == id_attr).exists()
        stmt = stmt.filter(subq if is_parent else ~subq)
    return stmt


def filter_is_child(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    parent_column: str = "parent_id",
    is_child: OptBool = None,
) -> Select[RowT]:
    parent_attr = getattr(table, parent_column, None)
    if parent_attr is None or not isinstance(parent_attr, InstrumentedAttribute):
        return stmt
    if is_child is not None:
        stmt = stmt.filter(
            parent_attr.is_not(None) if is_child else parent_attr.is_(None)
        )
    return stmt


def filter_is_leaf(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    id_column: str = "id",
    parent_column: str = "parent_id",
    is_leaf: OptBool = None,
) -> Select[RowT]:
    id_attr = getattr(table, id_column, None)
    if id_attr is None or not isinstance(id_attr, InstrumentedAttribute):
        return stmt
    parent_attr = getattr(table, parent_column, None)
    if parent_attr is None or not isinstance(parent_attr, InstrumentedAttribute):
        return stmt
    if is_leaf is not None:
        child_table = aliased(table)
        child_parent_attr = getattr(child_table, parent_column)
        subq = select(child_table).filter(child_parent_attr == id_attr).exists()
        stmt = stmt.filter(~subq if is_leaf else subq)
    return stmt


def search(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    search: OptStr = None,
    columns: OptListOfStrs = None,
) -> Select[RowT]:
    if search is None:
        return stmt

    search_term = f"%{search}%"
    sqla_table = table.__table__
    search_filters = []

    for name, attr in vars(table).items():
        if not isinstance(attr, InstrumentedAttribute):
            continue

        try:
            column = sqla_table.columns[name]
        except KeyError:
            continue

        if columns is not None and name not in columns:
            continue

        if isinstance(column.type, (String, TEXT)):
            search_filters.append(cast(attr, TEXT).ilike(search_term))

    if search_filters:
        stmt = stmt.filter(or_(*search_filters))

    return stmt


def sort(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    sort_columns: Sequence[SortColumn],
) -> Select[RowT]:
    for sort_column in sort_columns:
        try:
            sort_col = getattr(table, sort_column.name)
            sort_col = (
                asc(sort_col) if sort_column.order is Order.ASC else desc(sort_col)
            )
            stmt = stmt.order_by(sort_col)
        except AttributeError:
            continue
    return stmt


def paginate(stmt: Select[RowT], page: int, limit: int) -> Select[RowT]:
    offset: int = int((page - 1) * limit)
    stmt = stmt.limit(limit).offset(offset)
    return stmt
