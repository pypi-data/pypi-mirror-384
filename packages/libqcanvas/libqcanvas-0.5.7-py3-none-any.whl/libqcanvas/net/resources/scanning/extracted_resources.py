from dataclasses import dataclass

import libqcanvas.database.tables as db


@dataclass(slots=True)
class ExtractedResources:
    content: db.AnyContentItem
    resources: list[db.Resource]
    invisible_resources: list[db.Resource]
