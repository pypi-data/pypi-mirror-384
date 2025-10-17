from datetime import datetime
from typing import Sequence

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libqcanvas.database.resource_links import (
    WithAttachmentsOrnamentalMixin,
    WithResourcesOrnamentalMixin,
    with_attachments,
    with_embedded_resources,
)
from libqcanvas.database.tables.base import Base
from libqcanvas.database.tables.course_content_item import CourseContentItem
from libqcanvas.database.tables.creation_date import CreationDate
from libqcanvas.database.tables.id import ID
from libqcanvas.database.tables.modification_date import ModificationDate
from libqcanvas.database.tables.module_page_type import ModulePageType
from libqcanvas.database.tables.resource import Resource


@with_attachments
class SubmissionComment(
    Base, ID, CreationDate, ModificationDate, WithAttachmentsOrnamentalMixin
):
    __tablename__ = "submission_comments"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    course: Mapped["Course"] = relationship()
    group_id: Mapped[str] = mapped_column(ForeignKey("assignment_groups.id"))
    group: Mapped["AssignmentGroup"] = relationship()
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    assignment: Mapped["Assignment"] = relationship()
    submission_id: Mapped[str] = mapped_column(ForeignKey("assignment_submissions.id"))
    submission: Mapped["AssignmentSubmission"] = relationship(back_populates="comments")

    author: Mapped[str]
    body: Mapped[str]


@with_attachments
class AssignmentSubmission(
    Base, ID, CreationDate, ModificationDate, WithAttachmentsOrnamentalMixin
):
    __tablename__ = "assignment_submissions"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    course: Mapped["Course"] = relationship()
    group_id: Mapped[str] = mapped_column(ForeignKey("assignment_groups.id"))
    group: Mapped["AssignmentGroup"] = relationship()
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")

    comments: Mapped[list["SubmissionComment"]] = relationship(
        back_populates="submission", order_by=SubmissionComment.creation_date
    )

    attempt: Mapped[int]
    score: Mapped[float | None]


@with_embedded_resources
class Assignment(
    Base, CourseContentItem, ModificationDate, WithResourcesOrnamentalMixin
):
    __tablename__ = "assignments"

    group_id: Mapped[str] = mapped_column(ForeignKey("assignment_groups.id"))
    group: Mapped["AssignmentGroup"] = relationship(back_populates="assignments")

    submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="assignment", order_by=AssignmentSubmission.creation_date
    )

    due_date: Mapped[datetime | None]
    max_score: Mapped[float | None]
    position: Mapped[int]


class AssignmentGroup(Base, ID):
    __tablename__ = "assignment_groups"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    course: Mapped["Course"] = relationship(back_populates="assignment_groups")

    assignments: Mapped[list[Assignment]] = relationship(
        back_populates="group",
        order_by=Assignment.position,
        cascade="save-update, merge, delete",
    )

    name: Mapped[str]
    group_weight: Mapped[int]
    position: Mapped[int]

    @property
    def items(self) -> Sequence:
        return self.assignments


@with_attachments
@with_embedded_resources
class Message(
    Base,
    CourseContentItem,
    WithAttachmentsOrnamentalMixin,
    WithResourcesOrnamentalMixin,
):
    """
    Used for announcements and course mail
    """

    __tablename__ = "messages"

    sender_name: Mapped[str]
    has_been_read: Mapped[bool]
    course: Mapped["Course"] = relationship(back_populates="messages")


@with_embedded_resources
class Page(Base, CourseContentItem, ModificationDate, WithResourcesOrnamentalMixin):
    __tablename__ = "pages"

    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"))
    module: Mapped["Module"] = relationship(back_populates="pages")
    position: Mapped[int]
    page_type: Mapped[ModulePageType]


class Module(Base, ID):
    __tablename__ = "modules"

    name: Mapped[str]
    position: Mapped[int]
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    course: Mapped["Course"] = relationship(back_populates="modules")

    pages: Mapped[list["Page"]] = relationship(
        back_populates="module",
        order_by=Page.position,
        cascade="save-update, merge, delete",
    )

    @property
    def items(self) -> Sequence[CourseContentItem]:
        return self.pages


class Course(Base, ID):
    __tablename__ = "courses"

    name: Mapped[str]
    panopto_folder_id: Mapped[str | None]
    term_id: Mapped[str] = mapped_column(ForeignKey("terms.id"))
    term: Mapped["Term"] = relationship(back_populates="courses")

    assignment_groups: Mapped[list[AssignmentGroup]] = relationship(
        back_populates="course",
        order_by=AssignmentGroup.position,
        cascade="save-update, merge, delete",
    )
    modules: Mapped[list["Module"]] = relationship(
        back_populates="course",
        order_by=Module.position,
        cascade="save-update, merge, delete",
    )
    messages: Mapped[list[Message]] = relationship(
        viewonly=True,
        order_by=Message.creation_date,
    )
    resources: Mapped[list[Resource]] = relationship(
        back_populates="course",
        order_by=Resource.discovery_date,
        cascade="save-update, merge, delete",
    )


class Term(Base, ID):
    __tablename__ = "terms"

    start_date: Mapped[datetime | None]
    end_date: Mapped[datetime | None]
    name: Mapped[str]

    courses: Mapped[list["Course"]] = relationship(
        back_populates="term",
        order_by=Course.name,
        cascade="save-update, merge, delete",
    )

    def __hash__(self):
        return (
            hash(self.id)
            ^ hash(self.start_date)
            ^ hash(self.end_date)
            ^ hash(self.name)
        )
