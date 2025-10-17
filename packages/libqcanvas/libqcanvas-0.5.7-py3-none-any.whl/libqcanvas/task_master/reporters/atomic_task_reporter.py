import logging
from typing import Self

from libqcanvas.task_master.task_master import Reporter

_logger = logging.getLogger(__name__)


class AtomicTaskReporter(Reporter):
    """
    An atomic task reporter reports the completion of a task that is only 1 'step'.
    For example:

    tm = MyTaskMaster()
    with tm.accept(AtomicTaskReporter("My task", "First step")):
        # Task started
        await do_something()
        # Task complete
    """

    def __init__(self, goal_name: str, step_name: str):
        super().__init__(goal_name, step_name)

    def start(self) -> None:
        self.ensure_task_master_assigned()
        self.task_master.report_progress(self.task_id, 0, 0)

    def finish(self) -> None:
        self.ensure_task_master_assigned()
        self.task_master.report_progress(self.task_id, 1, 1)

    def __enter__(self) -> Self:
        self.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self.failed(exc_val)
        else:
            self.finish()
