from typing import Protocol, Sequence

from sqlalchemy.orm import Mapped

from libqcanvas.database.tables import CourseContentItem


class ContentGroup(Protocol):
    id: Mapped[str]
    name: Mapped[str]

    @property
    def items(self) -> Sequence[CourseContentItem]: ...
