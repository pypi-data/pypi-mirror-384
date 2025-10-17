from sqlalchemy.orm import Mapped

from libqcanvas.database.tables import Resource

class WithResourcesOrnamentalMixin:
    resources: Mapped[list[Resource]]
    dead_resources: Mapped[list[Resource]]

class WithAttachmentsOrnamentalMixin:
    attachments: Mapped[list[Resource]]
