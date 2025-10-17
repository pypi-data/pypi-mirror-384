from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from libqcanvas.database.tables._tz_datetime import TZDateTime


class Base(DeclarativeBase, AsyncAttrs, MappedAsDataclass, init=False):
    type_annotation_map = {datetime: TZDateTime}
