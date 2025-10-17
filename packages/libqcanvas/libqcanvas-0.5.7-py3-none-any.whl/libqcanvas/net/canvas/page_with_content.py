from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from libqcanvas.gql_queries import Module, ShallowCourse


@dataclass
class PageWithContent:
    q_id: str
    updated_at: Optional[datetime]
    created_at: Optional[datetime]
    module: Module
    course: ShallowCourse
    position: int
    name: Optional[str] = None
    content: Optional[str] = None
    is_locked: bool = False
    unlock_at: Optional[datetime] = None
    lock_at: Optional[datetime] = None
