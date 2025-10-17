import asyncio
import logging
from datetime import datetime
from typing import Sequence

from gql import gql
from libqcanvas_clients.canvas import CanvasClient

from libqcanvas import gql_queries
from libqcanvas.gql_queries import (
    Assignment,
    AssignmentGroup,
    AssignmentGroupIndexQueryData,
    AssignmentIndexQueryData,
    ConversationParticipant,
    CourseIndexQueryData,
    CourseMailQueryData,
    Module,
    ModuleIndexQueryData,
    ShallowCourse,
    Term,
)
from libqcanvas.net.canvas.course_bundle import CourseBundle
from libqcanvas.net.canvas.course_mail_item import CourseMailItem
from libqcanvas.net.constants import SYNC_GOAL
from libqcanvas.task_master import register_reporter
from libqcanvas.task_master.reporters import AtomicTaskReporter, CompoundTaskReporter
from libqcanvas.util import CollectingTaskGroup, flatten

_logger = logging.getLogger(__name__)


class CanvasDataAggregator:
    def __init__(self, canvas_client: CanvasClient):
        self._canvas_client = canvas_client

    async def pull_user_id(self) -> str:
        return await self._canvas_client.get_current_user_id()

    async def get_all_course_mail(self, current_user_id: str) -> list[CourseMailItem]:
        _logger.info("Fetching all course mail")

        with register_reporter(AtomicTaskReporter(SYNC_GOAL, "Fetch course mail")):
            result = await self._gql_query(
                gql_queries.COURSE_MAIL_QUERY, user_id=current_user_id
            )

        raw_mail_data = CourseMailQueryData(
            **result
        ).legacy_node.conversations_connection.nodes

        return self._convert_mail(raw_mail_data)

    @staticmethod
    def _convert_mail(
        raw_mail_data: list[ConversationParticipant],
    ):
        return [CourseMailItem.from_query_result(mail) for mail in raw_mail_data]

    async def pull_courses(
        self, already_indexed_course_ids: Sequence[str], include_old_courses: bool
    ) -> list[CourseBundle]:
        shallow_courses = await self._get_shallow_course_data()

        if len(shallow_courses) == 0:
            return []

        latest_term = self._find_latest_term(shallow_courses)

        courses_to_pull = [
            course
            for course in shallow_courses
            if self._course_belongs_to_term(course, latest_term)
            or (include_old_courses and course.q_id not in already_indexed_course_ids)
        ]

        return await self._pull_detailed_courses_by_id(courses_to_pull)

    @staticmethod
    def _course_belongs_to_term(course: ShallowCourse, term: Term) -> bool:
        return course.term.q_id == term.q_id

    async def _get_shallow_course_data(self) -> list[ShallowCourse]:
        with register_reporter(AtomicTaskReporter(SYNC_GOAL, "Fetch course indexes")):
            result = await self._gql_query(gql_queries.COURSE_INDEX_QUERY)

        return CourseIndexQueryData(**result).all_courses

    async def _pull_detailed_courses_by_id(
        self, courses: list[ShallowCourse]
    ) -> list[CourseBundle]:
        if _logger.isEnabledFor(logging.INFO):
            _logger.info("Fetching index for courses:")
            for course in courses:
                _logger.info(f"> '{course.name}' (id={course.q_id})")

        if len(courses) == 0:
            return []

        with register_reporter(
            CompoundTaskReporter(SYNC_GOAL, "Fetch course data", len(courses))
        ) as prog:
            async with CollectingTaskGroup[CourseBundle]() as tg:
                for course in courses:
                    prog.attach(tg.create_task(self._fetch_course(course)))

        return tg.results

    async def _fetch_course(self, course: ShallowCourse) -> CourseBundle:
        # todo progress reporting could be a bit more fine grained here

        bundle = CourseBundle(course=course)

        async def assignments_task():
            nonlocal bundle
            bundle.assignment_groups = await self._fetch_assignment_groups(course.q_id)

            async with CollectingTaskGroup[list[Assignment]]() as tg:
                for assignment_group in bundle.assignment_groups:
                    tg.create_task(self._fetch_assignments(assignment_group.q_id))

            bundle.assignments = flatten(tg.results)

        async def modules_task():
            nonlocal bundle
            bundle.modules = await self._fetch_modules(course.q_id)

        await asyncio.gather(assignments_task(), modules_task())

        return bundle

    async def _fetch_assignment_groups(self, course_id: str) -> list[AssignmentGroup]:
        query_result = await self._gql_query(
            gql_queries.ASSIGNMENT_GROUP_INDEX_QUERY,
            course_id=course_id,
        )
        parsed_result = AssignmentGroupIndexQueryData(**query_result)

        if not parsed_result.legacy_node:
            return []

        return parsed_result.legacy_node.assignment_groups or []

    async def _fetch_assignments(self, group_id: str) -> list[Assignment]:
        query_result = await self._gql_query(
            gql_queries.ASSIGNMENT_INDEX_QUERY, group_id=group_id
        )
        parsed_result = AssignmentIndexQueryData(**query_result)

        if (
            not parsed_result
            or not parsed_result.node
            or not parsed_result.node.assignments_connection
            or not parsed_result.node.assignments_connection.nodes
        ):
            return []

        return list(filter(None, parsed_result.node.assignments_connection.nodes))

    async def _fetch_modules(self, course_id: str) -> list[Module]:
        query_result = await self._gql_query(
            gql_queries.MODULE_INDEX_QUERY, course_id=course_id
        )
        parsed_result = ModuleIndexQueryData(**query_result)

        if (
            not parsed_result.legacy_node
            or not parsed_result.legacy_node.modules_connection
            or not parsed_result.legacy_node.modules_connection.nodes
        ):
            return []

        return list(filter(None, parsed_result.legacy_node.modules_connection.nodes))

    async def _gql_query(self, query: str, **kwargs):
        return await self._canvas_client.graphql_query(gql(query), kwargs)

    @staticmethod
    def _find_latest_term(courses: list[ShallowCourse]) -> Term:
        terms = [course.term for course in courses if course.term is not None]
        # For terms that don't have an end date (for whatever reason), just put them at the end of the list.
        # Don't use datetime.min because it can cause errors when doing timezone maths
        default_end_at = datetime.fromisoformat("1900-01-01T00:00:00Z")
        sorted_terms = sorted(terms, key=lambda term: term.end_at or default_end_at)

        return sorted_terms[-1]
