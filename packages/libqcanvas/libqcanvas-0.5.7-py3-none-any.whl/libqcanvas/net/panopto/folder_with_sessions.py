from dataclasses import dataclass

from libqcanvas_clients.panopto import FolderInfo, Session


@dataclass
class FolderWithSessions:
    folder: FolderInfo
    sessions: list[Session]
