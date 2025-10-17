import logging
from collections import defaultdict
from typing import Literal, Protocol, Sequence, runtime_checkable

from sqlalchemy import Table, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from libqcanvas.database.tables.resource import Resource

_logger = logging.getLogger(__name__)


type LinkType = Literal["embedded", "attachment"]
type LinkState = Literal["residual", "active"]


@runtime_checkable
class HasEmbeddedResources(Protocol):
    __tablename__: str
    __resource_link_table__: Table
    id: object


@runtime_checkable
class HasAttachments(Protocol):
    __tablename__: str
    __attachment_link_table__: Table
    id: object


def _get_content_link_table(content_item: object | type, link_type: LinkType) -> Table:
    if link_type == "embedded":
        if isinstance(content_item, HasEmbeddedResources):
            return content_item.__resource_link_table__
        else:
            raise TypeError("content_item does not support embedded resources")
    elif link_type == "attachment":
        if isinstance(content_item, HasAttachments):
            return content_item.__attachment_link_table__
        else:
            raise TypeError("content_item does not support attachments")
    else:
        raise ValueError("link_type")


def _validate_link_type(link_type: str) -> None:
    if link_type not in ["embedded", "attachment"]:
        raise ValueError(f"link_type: {link_type}")


def _validate_link_state(link_state: str) -> None:
    if link_state not in ["active", "residual"]:
        raise ValueError(f"link_state: {link_state}")


async def create_resource_link(
    session: AsyncSession,
    content_item: object,
    resource: Resource,
    *,
    link_type: LinkType = "embedded",
    link_state: LinkState = "active",
) -> None:
    await create_resource_link_a(
        session,
        content_id=content_item.id,
        content_type=content_item,
        resource=resource,
        link_type=link_type,
        link_state=link_state,
    )


# todo what the hell am I supposed to call this?? i wish python had overloading
async def create_resource_link_a[T](
    session: AsyncSession,
    *,
    content_id: object,
    content_type: type[T] | object,
    resource: Resource,
    link_type: LinkType = "embedded",
    link_state: LinkState = "active",
) -> None:
    table = _get_content_link_table(content_type, link_type)
    query_params = dict(content_item_id=content_id, resource_id=resource.id)

    if link_type == "embedded":
        _validate_link_state(link_state)
        query_params["link_state"] = link_state
    elif link_type == "attachment":
        if link_state != "active":
            raise ValueError("attachments do not support link_state")

    stmt = (
        insert(table)
        .values(**query_params)
        .on_conflict_do_nothing(index_elements=["content_item_id", "resource_id"])
    )
    await session.execute(stmt)


async def get_associated_resource_ids(
    session: AsyncSession, content_item: object, *, link_type: LinkType = "embedded"
) -> Sequence[str]:
    table = _get_content_link_table(content_item, link_type)
    stmt = select(table.c.resource_id).where(table.c.content_item_id == content_item.id)
    return (await session.scalars(stmt)).all()


async def change_embedded_link_state(
    session: AsyncSession,
    content_item: object,
    resource: Resource,
    *,
    link_state: LinkState,
) -> None:
    if not isinstance(content_item, HasEmbeddedResources):
        raise TypeError("content_item")

    _validate_link_state(link_state)

    link_table = content_item.__resource_link_table__
    stmt = (
        update(link_table)
        .where(link_table.c.resource_id == resource.id)
        .values(link_state=link_state)
    )
    await session.execute(stmt)


async def bulk_change_embedded_link_states(
    session: AsyncSession,
    content_items: list[HasEmbeddedResources],
    *,
    link_state: LinkState,
) -> None:
    _validate_link_state(link_state)
    content_grouped_by_link_table: dict[Table, set] = defaultdict(set)

    for item in content_items:
        if not isinstance(item, HasEmbeddedResources):
            raise TypeError(item)

        content_grouped_by_link_table[item.__resource_link_table__].add(item.id)

    for link_table, content_ids in content_grouped_by_link_table.items():
        stmt = (
            update(link_table)
            .where(link_table.c.content_item_id.in_(content_ids))
            .values(link_state=link_state)
        )
        await session.execute(stmt)
