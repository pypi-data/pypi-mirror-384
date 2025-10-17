from .canvas_database_types import (
    Assignment,
    AssignmentGroup,
    AssignmentSubmission,
    Course,
    CourseContentItem,
    Message,
    ModificationDate,
    Module,
    Page,
    SubmissionComment,
    Term,
)
from .content_group import ContentGroup
from .module_page_type import ModulePageType
from .resource import PanoptoResource, Resource
from .resource_download_state import ResourceDownloadState
from .resource_link_state import ResourceLinkState

type AnyContentItem = Assignment | Message | Page
