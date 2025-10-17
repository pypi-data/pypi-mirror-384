import logging
from abc import ABC, abstractmethod

from libqcanvas.task_master.task_id import TaskID

_logger = logging.getLogger(__name__)


class Reporter:
    """
    A reporter reports the progress of a task to a task master
    """

    def __init__(self, goal_name: str, step_name: str):
        self.task_master: TaskMaster | None = None
        self.task_id = TaskID(goal_name, step_name)

    def ensure_task_master_assigned(self) -> None:
        if self.task_master is None:
            raise Exception("Reporter has not been assigned to any task master yet")

    def failed(self, context: str | Exception) -> None:
        self.ensure_task_master_assigned()
        self.task_master.report_failed(self.task_id, context)

    def progress(self, current: int, total: int) -> None:
        self.ensure_task_master_assigned()
        assert current <= total
        self.task_master.report_progress(self.task_id, current, total)


class TaskMaster(ABC):
    """
    A task master is the central entity that task progress is reported to from reporters
    """

    @abstractmethod
    def report_failed(self, task_id: TaskID, context: str | Exception) -> None: ...

    @abstractmethod
    def report_progress(self, task_id: TaskID, current: int, total: int) -> None:
        """
        Implementations can expect:
        - TaskID for a specific task to always be the same
        - For intermediate tasks to be reported as (current=0, total=0)
        - For total to change as the task progresses
        - For finished tasks to be reported as current = total (unless total = 0, in which case it is an intermediate task)
        :param task_id:
        :param current:
        :param total:
        :return:
        """

    def accept[T: Reporter](self, reporter: T) -> T:
        reporter.task_master = self
        return reporter
