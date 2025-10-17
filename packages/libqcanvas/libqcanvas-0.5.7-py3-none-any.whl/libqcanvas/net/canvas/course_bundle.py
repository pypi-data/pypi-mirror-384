import logging
from dataclasses import dataclass, field

from libqcanvas.gql_queries import Assignment, AssignmentGroup, Module, ShallowCourse

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CourseBundle:
    course: ShallowCourse
    assignment_groups: list[AssignmentGroup] = field(default_factory=list)
    assignments: list[Assignment] = field(default_factory=list)
    modules: list[Module] = field(default_factory=list)
