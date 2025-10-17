import logging
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libqcanvas.database.tables.base import Base
from libqcanvas.database.tables.id import ID
from libqcanvas.database.tables.resource_download_state import ResourceDownloadState

_logger = logging.getLogger(__name__)


# noinspection PyDataclass
class Resource(Base, ID):
    __tablename__ = "resources"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id"))
    course = relationship("Course", back_populates="resources")

    url: Mapped[str]
    file_name: Mapped[str]
    # default_factory won't work here because init=False
    discovery_date: Mapped[datetime]
    file_size: Mapped[int | None]
    download_state: Mapped[ResourceDownloadState] = mapped_column(
        default=ResourceDownloadState.NOT_DOWNLOADED
    )
    download_error_message: Mapped[str | None]

    polymorphic_type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_on": "polymorphic_type",
        "polymorphic_identity": "resource",
    }


# noinspection PyDataclass
class PanoptoResource(Resource):
    __tablename__ = "panopto_resources"

    id: Mapped[str] = mapped_column(ForeignKey("resources.id"), primary_key=True)

    duration_seconds: Mapped[int]
    recording_date: Mapped[datetime]

    # Panopto/Canvas have this stupid "custom_context_delivery" which is a pain in the ass because it has nothing to do
    # with the actual ID of the video. In this case, this object's id may not be useful in any way (thanks painopto),
    # but delivery_id will always be the true ID of the video.
    # !!!! It has been observed that different "custom_context_delivery"s CAN link to the same video !!!!
    delivery_id: Mapped[str]

    __mapper_args__ = {"polymorphic_identity": "panopto_resource"}
