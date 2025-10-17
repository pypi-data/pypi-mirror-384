import difflib
import logging
import re
from typing import Tuple

from libqcanvas_clients.panopto import FolderInfo, PanoptoClient

import libqcanvas.gql_queries as gql
from libqcanvas.net.panopto.folder_with_sessions import FolderWithSessions

_logger = logging.getLogger(__name__)


class PanoptoDataAggregator:
    _course_name_cleaner_pattern = re.compile(r"(.+?) \(")

    def __init__(self, panopto_client: PanoptoClient):
        self._panopto_client = panopto_client

    async def get_course_panopto_folders(
        self, courses: list[gql.ShallowCourse]
    ) -> dict[str, str]:
        """
        Identifies the panopto folder for each course specified.
        :param courses: The courses for which to find the panopto folder
        :return: Dict of course_id -> folder_id
        """
        _logger.info("Fetching panopto folder index")

        result = {}
        folders = await self.get_folders()
        course_map = {
            self._formatted_course_name(course): course.q_id for course in courses
        }

        for folder in folders:
            try:
                clean_name = self._clean_course_name(folder.name)
                closest_match = difflib.get_close_matches(
                    clean_name, course_map.keys(), 1
                )[0]
            except IndexError:
                _logger.debug(
                    'No folder "%s" has no close match. If this is a partial sync, this is expected.',
                    folder.name,
                )
                continue
            except ValueError:
                _logger.info('Folder "%s" has invalid name, ignoring', folder.name)
                continue

            course_id = course_map[closest_match]
            result[course_id] = folder.id

            _logger.debug(
                "Matched panopto folder '%s' (id='%s') to course id='%s'",
                folder.name,
                folder.id,
                course_id,
            )

        return result

    def _formatted_course_name(self, course: gql.ShallowCourse) -> str:
        clean_name = self._clean_course_name(course.name)
        return f"{course.term.name} - {clean_name}"

    def _clean_course_name(self, name: str) -> str:
        # Remove course codes, semester name and campus information from a course/folder name
        match = self._course_name_cleaner_pattern.search(name)

        if match is None:
            raise ValueError()

        return match.group(1)

    async def _get_lectures_task(
        self, folder: FolderInfo, course_id: str
    ) -> Tuple[str, FolderWithSessions]:
        sessions = await self._panopto_client.get_folder_sessions(folder.id)
        return course_id, FolderWithSessions(folder=folder, sessions=sessions.results)

    async def get_folders(self) -> list[FolderInfo]:
        folders = await self._panopto_client.get_folders()
        return self._discard_parent_folders(folders)

    @staticmethod
    def _discard_parent_folders(folders: list[FolderInfo]) -> list[FolderInfo]:
        def predicate(folder: FolderInfo) -> bool:
            return not folder.has_accessible_children

        return list(filter(predicate, folders))
