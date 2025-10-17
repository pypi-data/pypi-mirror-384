import logging
from typing import NamedTuple

_logger = logging.getLogger(__name__)


class TaskID(NamedTuple):
    goal_name: str
    step_name: str
