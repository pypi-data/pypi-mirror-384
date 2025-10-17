from dataclasses import dataclass

from libqcanvas_clients.canvas import Announcement

from libqcanvas.net.canvas import CourseMailItem, PageWithContent
from libqcanvas.net.canvas.course_bundle import CourseBundle


@dataclass
class CanvasDataBundle:
    """
    A CanvasDataBundle is a collection of various data retrieved from canvas
    """

    courses: list[CourseBundle]
    pages: list[PageWithContent]
    messages: list[CourseMailItem | Announcement]
    course_panopto_folders: dict[str, str]
