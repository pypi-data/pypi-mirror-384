from operator import and_

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import relationship

from libqcanvas.database.tables.base import Base
from libqcanvas.database.tables.resource import Resource


def with_embedded_resources[T](cls: type[T]) -> type[T]:
    if hasattr(cls, "__tablename__"):
        tablename: str = cls.__tablename__
        link_table = Table(
            f"{tablename}_resource_links",
            Base.metadata,
            Column(
                "content_item_id",
                ForeignKey(f"{tablename}.id"),
                primary_key=True,
            ),
            Column("resource_id", ForeignKey("resources.id"), primary_key=True),
            Column("link_state", String),
        )
        cls.__resource_link_table__ = link_table
        cls.resources = relationship(
            Resource,
            secondary=link_table,
            primaryjoin=and_(
                link_table.c.content_item_id == cls.id,
                link_table.c.link_state == "active",
            ),
            order_by=Resource.id,
            overlaps="dead_resources",
            viewonly=True,
        )
        cls.dead_resources = relationship(
            Resource,
            secondary=link_table,
            primaryjoin=and_(
                link_table.c.content_item_id == cls.id,
                link_table.c.link_state == "residual",
            ),
            order_by=Resource.id,
            overlaps="resources",
            viewonly=True,
        )
    else:
        raise RuntimeError()

    return cls


def with_attachments[T](cls: type[T]) -> type[T]:
    if hasattr(cls, "__tablename__"):
        tablename: str = cls.__tablename__
        link_table = Table(
            f"{tablename}_attachment_links",
            Base.metadata,
            Column(
                "content_item_id",
                ForeignKey(f"{tablename}.id"),
                primary_key=True,
            ),
            Column("resource_id", ForeignKey("resources.id"), primary_key=True),
        )
        cls.__attachment_link_table__ = link_table
        cls.attachments = relationship(
            Resource,
            secondary=link_table,
            primaryjoin=link_table.c.content_item_id == cls.id,
            order_by=Resource.id,
            viewonly=True,
        )
    else:
        raise RuntimeError()

    return cls
