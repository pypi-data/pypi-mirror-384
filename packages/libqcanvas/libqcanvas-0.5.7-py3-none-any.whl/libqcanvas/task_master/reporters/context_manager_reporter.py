import logging
from typing import Self

from libqcanvas.task_master.task_master import Reporter

_logger = logging.getLogger(__name__)


# todo: merge into base Reporter, not really any reason to have this functionality separate
class ContextManagerReporter(Reporter):
    """
    Report the progress of a task where the progress is a number with an upper limit

    Example:
    tm = MyTaskMaster()

    # Report the progress of some task with an incrementing number
    with tm.accept(ContextManagerReporter("My demo", "Count to 10", 10)) as prog:
        for i in range(0, 11):
            prog.progress(i)

    """

    def __init__(self, goal_name: str, step_name: str, total_work: int):
        super().__init__(goal_name, step_name)
        self._total = total_work

    def __enter__(self) -> Self:
        self.ensure_task_master_assigned()
        self.progress(0, self._total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self.failed(exc_val)
