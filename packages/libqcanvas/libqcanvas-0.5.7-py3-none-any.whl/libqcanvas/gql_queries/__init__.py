from .assignment_group_index import AssignmentGroup, AssignmentGroupIndexQueryData
from .assignment_group_index import DEFINITION as ASSIGNMENT_GROUP_INDEX_QUERY
from .assignment_index import (
    Assignment,
    AssignmentIndexQueryData,
    Submission,
    SubmissionComment,
    SubmissionCommentConnection,
    SubmissionConnection,
)
from .assignment_index import DEFINITION as ASSIGNMENT_INDEX_QUERY
from .attachment import Attachment
from .course_index import Course as ShallowCourse
from .course_index import CourseIndexQueryData, Term
from .course_index import DEFINITION as COURSE_INDEX_QUERY
from .course_mail import ConversationParticipant, CourseMailQueryData
from .course_mail import DEFINITION as COURSE_MAIL_QUERY
from .module_index import DEFINITION as MODULE_INDEX_QUERY
from .module_index import (
    File,
    Module,
    ModuleConnection,
    ModuleIndexQueryData,
    ModuleItem,
    Page,
)
