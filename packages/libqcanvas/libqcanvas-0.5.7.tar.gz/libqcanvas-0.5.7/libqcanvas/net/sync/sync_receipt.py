import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Self, override

import libqcanvas.database.tables as db
from libqcanvas.net.sync.canvas_sync_observer import CanvasSyncObserver

_logger = logging.getLogger(__name__)


@dataclass
class CourseUpdates:
    updates: dict[type, set[str | int]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def new_content_found(self, content: object) -> None:
        if isinstance(content, db.Module):
            self.updates[db.Module].add(content.id)
        elif isinstance(content, db.Page):
            self.updates[db.Page].add(content.id)
            self.updates[db.Module].add(content.module_id)
        elif isinstance(content, db.Message):
            self.updates[db.Message].add(content.id)
        elif isinstance(content, db.AssignmentGroup):
            self.updates[db.AssignmentGroup].add(content.id)
        elif isinstance(content, db.Assignment):
            self.updates[db.Assignment].add(content.id)
            self.updates[db.AssignmentGroup].add(content.group_id)
        elif isinstance(content, db.AssignmentSubmission):
            self.updates[db.AssignmentSubmission].add(content.id)
            self.updates[db.AssignmentGroup].add(content.group_id)
            self.updates[db.Assignment].add(content.assignment_id)
        elif isinstance(content, db.SubmissionComment):
            self.updates[db.SubmissionComment].add(content.id)
            self.updates[db.AssignmentSubmission].add(content.submission_id)
            self.updates[db.AssignmentGroup].add(content.group_id)
            self.updates[db.Assignment].add(content.assignment_id)
        elif isinstance(content, db.Resource):
            self.updates[db.Resource].add(content.id)
        else:
            _logger.warning(
                "Content of type %s was not properly handled by the sync receipt tracker!",
                type(content).__name__,
            )

    def was_updated(self, content: object) -> bool:
        content_type = type(content)

        if hasattr(content, "id"):
            if content_type in self.updates:
                return content.id in self.updates[content_type]
        else:
            _logger.warning(
                "Object without `id` attr passed to `was_updated` (type=%s)",
                content_type.__name__,
            )

        return False

    def finalise(self) -> None:
        """
        Finalises the updates list.
        Converts the `updates` `defaultdict` into a regular dictionary to make it harder to accidentally add something to it
        """
        self.updates = dict(self.updates)

    def __getitem__(self, item: type) -> set[str | int] | None:
        if not isinstance(item, type):
            raise TypeError("item")

        return self.updates.get(item, None)


@dataclass
class SyncReceipt(CanvasSyncObserver, CourseUpdates):
    updates_by_course: dict[str, CourseUpdates] = field(
        default_factory=lambda: defaultdict(CourseUpdates)
    )

    def new_content_found(self, content: object) -> None:
        if isinstance(content, db.Course):
            self.updates[db.Course].add(content.id)
        else:
            # Need to specify CourseUpdates because of the diamond problem
            CourseUpdates.new_content_found(self, content)

            if hasattr(content, "course_id"):
                if content.course_id not in self.updates_by_course:
                    self.updates[db.Course].add(content.course_id)

                self.updates_by_course[content.course_id].new_content_found(content)

    @override
    def finalise(self) -> Self:
        """
        Finalises the sync receipt.
        Converts all `defaultdict`s to regular dictionaries to make it harder to accidentally add things to them
        """
        self.updates_by_course = dict(self.updates_by_course)

        for value in self.updates_by_course.values():
            value.finalise()

        return self


_empty = SyncReceipt()
_empty.finalise()


def empty_receipt() -> SyncReceipt:
    """
    An empty sync receipt instance for calling functions that would normally require one from an antecedent sync operation
    """
    global _empty
    return _empty
