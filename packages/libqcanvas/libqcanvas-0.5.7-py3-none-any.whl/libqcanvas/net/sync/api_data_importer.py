import logging
from datetime import datetime
from typing import Any

import libqcanvas_clients.canvas as canvas
from sqlalchemy.ext.asyncio import AsyncSession

import libqcanvas.database.tables as db
import libqcanvas.gql_queries as gql
from libqcanvas.database import resource_links
from libqcanvas.database.tables import ModulePageType
from libqcanvas.net.canvas import CourseMailItem, PageWithContent
from libqcanvas.net.resources.extracting import CanvasFileExtractor
from libqcanvas.net.resources.extracting.link_extractor import LinkExtractor
from libqcanvas.net.sync.canvas_sync_observer import CanvasSyncObservable
from libqcanvas.util import (
    remove_screenreader_elements,
    remove_unwanted_whitespaces,
)

_logger = logging.getLogger(__name__)

NO_TITLE = "No Title"
NO_AUTHOR = "Unknown Author"


class APIDataImporter(CanvasSyncObservable):
    """
    An APIDataImporter accepts canvas API objects and converts and adds them to the database
    """

    _type_map = {
        gql.ShallowCourse: db.Course,
        gql.Term: db.Term,
        gql.Module: db.Module,
        gql.Assignment: db.Assignment,
        gql.AssignmentGroup: db.AssignmentGroup,
        gql.File: db.Page,
        gql.Submission: db.AssignmentSubmission,
        gql.SubmissionComment: db.SubmissionComment,
        PageWithContent: db.Page,
        CourseMailItem: db.Message,
        canvas.Announcement: db.Message,
    }

    def __init__(self, session: AsyncSession):
        super().__init__()
        self._session = session

    async def convert_and_store_course(
        self, course: gql.ShallowCourse, *, panopto_folder_id: str | None
    ) -> None:
        db_course: db.Course = await self._find_or_create_db_entry(course)
        is_new = _is_record_new(db_course)

        db_course.id = course.q_id
        db_course.name = remove_unwanted_whitespaces(course.name) or NO_TITLE
        db_course.term_id = course.term.q_id

        if panopto_folder_id is not None:
            db_course.panopto_folder_id = panopto_folder_id

        if is_new:
            self.notify_observers_for_updated_item(db_course)

    async def convert_and_store_module(
        self, module: gql.Module, *, course_id: str, position: int
    ) -> None:
        db_module: db.Module = await self._find_or_create_db_entry(module)

        is_new = _is_record_new(db_module)

        db_module.id = module.q_id
        db_module.name = module.name or NO_TITLE
        db_module.course_id = course_id
        db_module.position = position

        if is_new:
            self.notify_observers_for_updated_item(db_module)

    async def convert_and_store_page(self, page: PageWithContent) -> None:
        db_page: db.Page = await self._find_or_create_db_entry(page)

        if not (_is_record_new_or_updated(db_object=db_page, api_object=page)):
            # Updating the record is not going to do anything
            return

        db_page.id = page.q_id
        db_page.course_id = page.course.q_id
        db_page.module_id = page.module.q_id
        db_page.name = remove_unwanted_whitespaces(page.name) or NO_TITLE
        db_page.body = _clean_html_body(page.content)
        db_page.can_view = not page.is_locked
        db_page.unlock_at = page.unlock_at
        db_page.lock_at = page.lock_at
        db_page.creation_date = page.created_at
        db_page.last_modification_date = page.updated_at
        db_page.position = page.position
        db_page.page_type = ModulePageType.PAGE

        self.notify_observers_for_updated_item(db_page)

    async def convert_and_store_term(self, term: gql.Term) -> None:
        db_term: db.Term = await self._find_or_create_db_entry(term)

        is_new = _is_record_new(db_term)

        db_term.id = term.q_id
        db_term.end_date = term.end_at
        db_term.start_date = term.start_at
        db_term.name = remove_unwanted_whitespaces(term.name) or NO_TITLE

        if is_new:
            self.notify_observers_for_updated_item(db_term)

    async def convert_and_store_assignment_group(
        self, assignment_group: gql.AssignmentGroup, *, course_id: str, position: int
    ) -> None:
        db_group: db.AssignmentGroup = await self._find_or_create_db_entry(
            assignment_group
        )

        is_new = _is_record_new(db_group)

        db_group.id = assignment_group.q_id
        db_group.name = remove_unwanted_whitespaces(assignment_group.name) or NO_TITLE
        db_group.course_id = course_id
        db_group.group_weight = assignment_group.group_weight
        db_group.position = position

        if is_new:
            self.notify_observers_for_updated_item(db_group)

    async def convert_and_store_assignment(
        self, assignment: gql.Assignment, *, group_id: str
    ) -> None:
        db_assignment: db.Assignment = await self._find_or_create_db_entry(assignment)

        # Canvas creates bogus modtime updates, this tracks whether something was actually updated
        actually_updated = False
        can_view = assignment.lock_info.can_view or not assignment.lock_info.is_locked

        # check if the assignment has been unlocked since we last saved it
        if not _is_record_new(db_assignment):
            was_unlocked = not db_assignment.can_view and can_view
            actually_updated = was_unlocked

            if was_unlocked:
                _logger.debug(
                    "Assignment '%s' (id=%s) was unlocked",
                    assignment.name,
                    assignment.q_id,
                )
            elif not _is_api_object_newer(
                db_object=db_assignment, api_object=assignment
            ):
                # Updating the record is not going to do anything
                return

        _logger.debug(
            "Assignment %s (id=%s) was updated according to canvas",
            assignment.name,
            assignment.q_id,
        )

        # "boring" fields that don't really matter to the user if they're updated
        db_assignment.id = assignment.q_id
        db_assignment.course_id = assignment.course_id
        db_assignment.creation_date = assignment.created_at
        db_assignment.position = assignment.position
        db_assignment.group_id = group_id
        db_assignment.last_modification_date = assignment.updated_at

        db_assignment.can_view = can_view
        db_assignment.unlock_at = assignment.lock_info.unlock_at
        db_assignment.lock_at = assignment.lock_info.lock_at

        new_name = remove_unwanted_whitespaces(assignment.name) or NO_TITLE
        new_body = _clean_html_body(assignment.description)
        new_due_date = assignment.due_at
        new_max_score = assignment.points_possible

        # check if these fields are actually updated. Canvas seems to create bogus updates for assignments, possibly from
        # markers doing something in the background.

        if new_name != db_assignment.name:
            db_assignment.name = new_name
            actually_updated = True
            _logger.debug(
                "assignment name updated (name=%s, id=%s)",
                assignment.name,
                assignment.q_id,
            )

        if new_body != db_assignment.body:
            db_assignment.body = new_body
            actually_updated = True
            _logger.debug(
                "assignment body updated (name=%s, id=%s)",
                assignment.name,
                assignment.q_id,
            )

        if new_due_date != db_assignment.due_date:
            db_assignment.due_date = new_due_date
            actually_updated = True
            _logger.debug(
                "assignment due date updated (name=%s, id=%s)",
                assignment.name,
                assignment.q_id,
            )

        if new_max_score != db_assignment.max_score:
            db_assignment.max_score = new_max_score
            actually_updated = True
            _logger.debug(
                "assignment max score updated (name=%s, id=%s)",
                assignment.name,
                assignment.q_id,
            )

        if actually_updated:
            self.notify_observers_for_updated_item(db_assignment)
        else:
            _logger.debug(
                "Assignment %s (id=%s) wasn't actually modified",
                assignment.name,
                assignment.q_id,
            )

    async def convert_and_store_assignment_submission(
        self,
        submission: gql.Submission,
        *,
        assignment_id: str,
        group_id: str,
        course_id: str,
    ) -> None:
        db_submission: db.AssignmentSubmission = await self._find_or_create_db_entry(
            submission
        )

        if not _is_record_new_or_updated(db_submission, submission):
            return

        db_submission.id = submission.q_id

        db_submission.course_id = course_id
        db_submission.group_id = group_id
        db_submission.assignment_id = assignment_id

        db_submission.attempt = submission.attempt
        db_submission.last_modification_date = submission.updated_at
        db_submission.creation_date = submission.created_at
        db_submission.score = submission.score

        self.notify_observers_for_updated_item(db_submission)

    async def convert_and_store_submission_comment(
        self,
        comment: gql.SubmissionComment,
        *,
        assignment_id: str,
        group_id: str,
        course_id: str,
        submission_id: str,
    ):
        db_comment: db.SubmissionComment = await self._find_or_create_db_entry(comment)

        if not _is_record_new_or_updated(db_comment, comment):
            return

        db_comment.id = comment.q_id

        db_comment.course_id = course_id
        db_comment.group_id = group_id
        db_comment.assignment_id = assignment_id
        db_comment.submission_id = submission_id

        db_comment.body = comment.html_comment
        db_comment.author = comment.author.name
        db_comment.creation_date = comment.created_at
        db_comment.last_modification_date = comment.updated_at

        self.notify_observers_for_updated_item(db_comment)

    async def convert_and_store_announcement(
        self, announcement: canvas.Announcement
    ) -> None:
        db_message: db.Message = await self._find_or_create_db_entry(announcement)

        # Canvas doesn't seem to track last modification date on announcements for some reason
        # Otherwise, I would check for modification time here
        is_new = _is_record_new(db_message)

        db_message.id = str(announcement.id)
        db_message.course_id = announcement.course_id
        db_message.creation_date = announcement.created_at
        db_message.name = remove_unwanted_whitespaces(announcement.title) or NO_TITLE
        db_message.body = _clean_html_body(announcement.message)
        db_message.sender_name = announcement.user_name or NO_AUTHOR
        db_message.has_been_read = False

        # I don't think this will have any effect since the announcement just disappears when it's locked.
        db_message.can_view = announcement.locked_for_user
        db_message.lock_at = announcement.lock_at

        if is_new:
            self.notify_observers_for_updated_item(db_message)

    async def convert_and_store_attachment(
        self,
        attachment: canvas.RemoteFile | gql.Attachment,
        *,
        course_id: str,
        parent_api_object: Any,
    ) -> None:
        resource = _create_resource_from_attachment(attachment, course_id=course_id)

        if await self._add_resource_if_missing(resource):
            db_type = self._type_map[type(parent_api_object)]
            content_id = _id_from_api_object(parent_api_object)

            await resource_links.create_resource_link_a(
                self._session,
                content_type=db_type,
                content_id=content_id,
                resource=resource,
                link_type="attachment",
            )
            self.notify_observers_for_updated_item(resource)

    async def convert_and_store_mail_item(self, mail: CourseMailItem) -> None:
        db_message: db.Message = await self._find_or_create_db_entry(mail)

        is_new = _is_record_new(db_message)

        db_message.id = mail.id
        db_message.course_id = mail.course_id
        db_message.creation_date = mail.date
        db_message.name = remove_unwanted_whitespaces(mail.subject) or NO_TITLE
        db_message.body = _convert_plaintext_to_html(
            remove_unwanted_whitespaces(mail.body)
        )
        db_message.sender_name = mail.author_name or NO_AUTHOR
        db_message.has_been_read = False
        db_message.can_view = True  # I don't think mail can be locked

        if is_new:
            self.notify_observers_for_updated_item(db_message)

    async def _find_or_create_db_entry(self, obj: Any):
        obj_type = type(obj)

        if obj_type not in self._type_map.keys():
            raise TypeError(f"{obj_type} is not present in _type_map")

        obj_id = _id_from_api_object(obj)
        db_type = self._type_map[obj_type]
        db_object = await self._session.get(db_type, obj_id)

        if db_object is None:
            _logger.debug(
                'Converting new %s (api) to %s (db) (id="%s")',
                obj_type.__name__,
                db_type.__name__,
                obj_id,
            )
            db_object = db_type()
            self._session.add(db_object)
        else:
            _logger.debug(
                'Found existing %s (db) for %s (api) (id="%s")',
                db_type.__name__,
                obj_type.__name__,
                obj_id,
            )

        return db_object

    async def _add_resource_if_missing(self, resource: db.Resource) -> bool:
        does_not_exist = (await self._session.get(db.Resource, resource.id)) is None

        if does_not_exist:
            _logger.debug("New resource %s (id=%s)", resource.file_name, resource.id)
            self._session.add(resource)
            self.notify_observers_for_updated_item(resource)

        return does_not_exist


def _id_from_api_object(obj: Any) -> str | int | tuple[str, str]:
    # Sanity check
    if hasattr(obj, "q_id") and hasattr(obj, "id"):
        _logger.warning(f"!?!?!? {obj} has `q_id` AND `id`???")

    if hasattr(obj, "q_id"):
        return obj.q_id
    elif hasattr(obj, "id"):
        return obj.id
    else:
        raise TypeError(f"{type(obj)} can not be handled")


def _is_record_new_or_updated(
    db_object: object | db.ModificationDate, api_object: object
) -> bool:
    if _is_record_new(db_object):
        return True
    else:
        return _is_api_object_newer(db_object, api_object)


def _is_api_object_newer(
    db_object: object | db.ModificationDate, api_object: object
) -> bool:
    if (
        hasattr(api_object, "updated_at")
        and isinstance(api_object.updated_at, datetime)
        and isinstance(db_object.last_modification_date, datetime)
    ):
        return db_object.last_modification_date < api_object.updated_at
    else:
        return False


def _is_record_new(db_obj: object) -> bool:
    if hasattr(db_obj, "id"):
        return db_obj.id is None
    else:
        return False


def _clean_html_body(page: str) -> str:
    return remove_screenreader_elements(remove_unwanted_whitespaces(page))


def _convert_plaintext_to_html(plaintext: str) -> str:
    return plaintext.replace("\n", "<br/>\n")


def _create_resource_from_attachment(
    attachment: gql.Attachment | canvas.RemoteFile, *, course_id: str
) -> db.Resource:
    if hasattr(attachment, "q_id"):
        attachment_id = attachment.q_id
    else:
        attachment_id = attachment.id

    return db.Resource(
        id=f"{CanvasFileExtractor.extractor_id}{LinkExtractor.RESOURCE_ID_SEPARATOR}{attachment_id}",
        url=attachment.url,
        course_id=course_id,
        discovery_date=datetime.now().astimezone(),
        file_name=attachment.display_name,
    )
