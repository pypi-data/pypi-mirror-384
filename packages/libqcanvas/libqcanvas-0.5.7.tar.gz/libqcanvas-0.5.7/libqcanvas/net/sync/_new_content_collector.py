import libqcanvas.database.tables as db
from libqcanvas.net.sync.canvas_sync_observer import CanvasSyncObserver


class NewContentCollector(CanvasSyncObserver):
    def __init__(self):
        super().__init__()
        self._new_content: list[db.AnyContentItem] = []

    def new_content_found(self, content: object):
        if isinstance(content, db.CourseContentItem):
            self._new_content.append(content)

    @property
    def new_content(self) -> list[db.AnyContentItem]:
        return self._new_content
