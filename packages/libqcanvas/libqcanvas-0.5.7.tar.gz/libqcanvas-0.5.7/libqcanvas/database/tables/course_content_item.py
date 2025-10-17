from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from libqcanvas.database.tables.creation_date import CreationDate
from libqcanvas.database.tables.id import ID


class CourseContentItem(ID, CreationDate):
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))

    name: Mapped[str]
    body: Mapped[str | None]

    unlock_at: Mapped[datetime | None] = mapped_column(default=None)
    lock_at: Mapped[datetime | None] = mapped_column(default=None)
    # Tracks whether the page is locked
    can_view: Mapped[bool]
