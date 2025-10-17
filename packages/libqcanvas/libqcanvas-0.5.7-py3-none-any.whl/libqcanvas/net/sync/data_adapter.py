import logging

from libqcanvas_clients.canvas import Announcement

import libqcanvas.gql_queries as gql
from libqcanvas.net.canvas import CourseMailItem, PageWithContent
from libqcanvas.net.canvas.course_bundle import CourseBundle
from libqcanvas.net.constants import SYNC_GOAL
from libqcanvas.net.sync._canvas_data_bundle import CanvasDataBundle
from libqcanvas.net.sync.api_data_importer import APIDataImporter
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import AtomicTaskReporter

_logger = logging.getLogger(__name__)


class DataAdapter:
    """
    A DataAdapter deeply iterates over everything in a CanvasDataBundle and adds this data to the database using an APIDataImporter
    """

    def __init__(self, importer: APIDataImporter):
        self._converter = importer

    async def convert_and_add_to_database(self, canvas_sync_data: CanvasDataBundle):
        with register_reporter(AtomicTaskReporter(SYNC_GOAL, "Add data to database")):
            await self._store_partial_course_data(
                bundles=canvas_sync_data.courses,
                course_panopto_folders=canvas_sync_data.course_panopto_folders,
            )
            await self._store_pages(canvas_sync_data.pages)
            await self._store_messages(
                canvas_sync_data.messages,
                known_course_ids=[
                    bundle.course.q_id for bundle in canvas_sync_data.courses
                ],
            )

    async def _store_partial_course_data(
        self, bundles: list[CourseBundle], course_panopto_folders: dict[str, str]
    ):
        for term in self._flatten_terms(bundles):
            await self._converter.convert_and_store_term(term)

        for bundle in bundles:
            course_id = bundle.course.q_id
            await self._converter.convert_and_store_course(
                bundle.course,
                panopto_folder_id=course_panopto_folders.get(course_id, None),
            )

            for position, module in enumerate(bundle.modules):
                await self._converter.convert_and_store_module(
                    module, course_id=course_id, position=position
                )

            legacy_id_to_qgl_id: dict[str, str] = {}

            for position, assignment_group in enumerate(bundle.assignment_groups):
                # For some reason, assignment_group_id is a legacy ID despite being part of the newer graphql system.
                # Since assignment objects don't have the newer ID available, we need to store what it maps to.
                # An alternative to this would be to just use the legacy ID for assignment groups, but I would rather
                # just use the new ids where possible.
                legacy_id_to_qgl_id[assignment_group.legacy_id] = assignment_group.q_id

                await self._converter.convert_and_store_assignment_group(
                    assignment_group,
                    course_id=course_id,
                    position=position,
                )

            for assignment in bundle.assignments:
                group_id = legacy_id_to_qgl_id[assignment.assignment_group_id]

                await self._converter.convert_and_store_assignment(
                    assignment, group_id=group_id
                )

                for submission in assignment.submissions_connection.nodes:
                    await self._converter.convert_and_store_assignment_submission(
                        submission,
                        assignment_id=assignment.q_id,
                        course_id=course_id,
                        group_id=group_id,
                    )

                    for attachment in submission.attachments:
                        await self._converter.convert_and_store_attachment(
                            attachment,
                            course_id=course_id,
                            parent_api_object=submission,
                        )

                    for comment in submission.comments_connection.nodes:
                        await self._converter.convert_and_store_submission_comment(
                            comment,
                            course_id=course_id,
                            assignment_id=assignment.q_id,
                            group_id=group_id,
                            submission_id=submission.q_id,
                        )

                        for attachment in comment.attachments:
                            await self._converter.convert_and_store_attachment(
                                attachment,
                                course_id=course_id,
                                parent_api_object=comment,
                            )

    @staticmethod
    def _flatten_terms(bundles: list[CourseBundle]) -> list[gql.Term]:
        term_id_map: dict[str, gql.Term] = {}

        for bundle in bundles:
            term = bundle.course.term
            term_id_map[term.q_id] = term

        return list(term_id_map.values())

    async def _store_pages(self, pages: list[PageWithContent]):
        for page in pages:
            await self._converter.convert_and_store_page(page)

    async def _store_messages(
        self, messages: list[CourseMailItem | Announcement], known_course_ids: list[str]
    ):
        for message in messages:
            if isinstance(message, CourseMailItem):
                # Canvas includes mail for information "courses", but they're not visible in the allCourses graphql item.
                # Since they are not indexed anywhere else, we will discard them here
                if message.course_id in known_course_ids:
                    await self._converter.convert_and_store_mail_item(message)
                else:
                    _logger.debug(
                        'Discarding mail item "%s" (id="%s") because it\'s not in the list of courses for this sync (id="%s")',
                        message.subject,
                        message.id,
                        message.course_id,
                    )
            elif (
                isinstance(message, Announcement)
                and message.course_id in known_course_ids
            ):
                await self._converter.convert_and_store_announcement(message)

                for attachment in message.attachments:
                    await self._converter.convert_and_store_attachment(
                        attachment=attachment,
                        course_id=message.course_id,
                        parent_api_object=message,
                    )
