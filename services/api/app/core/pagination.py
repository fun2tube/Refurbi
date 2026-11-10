from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.settings import get_settings

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int | None, Query(ge=1)] = None,
) -> PageParams:
    s = get_settings()
    size = min(page_size or s.default_page_size, s.max_page_size)
    return PageParams(page=page, page_size=size)


PageDep = Annotated[PageParams, Depends(page_params)]


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


def make_page(items: list[T], total: int, params: PageParams) -> Page[T]:
    return Page[T](
        items=items,
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=ceil(total / params.page_size) if total else 0,
    )


def paginate(session: Session, stmt: Select, params: PageParams) -> tuple[list, int]:
    """Run a SELECT with LIMIT/OFFSET plus a count; returns (rows, total)."""
    total = session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = list(session.scalars(stmt.limit(params.page_size).offset(params.offset)))
    return rows, total
