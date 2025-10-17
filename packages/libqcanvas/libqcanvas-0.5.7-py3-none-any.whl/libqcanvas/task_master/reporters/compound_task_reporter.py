import logging
from asyncio import Task
from threading import Lock
from typing import Self

from libqcanvas.task_master.task_master import Reporter

_logger = logging.getLogger(__name__)


class CompoundTaskReporter(Reporter):
    """
    A compound task reporter reports the completion of a task that has several steps.
    It can also be used to track the completion of many closely related tasks.

    For example:
    tm = MyTaskMaster()

    urls = [f"https://jsonplaceholder.typicode.com/posts/{num}" for num in range(1, 11)]

    # Report the completion of tasks in a task group
    with tm.accept(CompoundTaskReporter("My demo", "Make requests", len(urls))) as prog:
        async with TaskGroup() as tg:
            for url in urls:
                prog.attach(tg.create_task(get_url_async(url)))
    """

    def __init__(self, goal_name: str, step_name: str, total_tasks: int):
        super().__init__(goal_name, step_name)
        self._lock = Lock()
        self._total_tasks = total_tasks
        self._complete_tasks = 0

    def __enter__(self) -> Self:
        self.ensure_task_master_assigned()
        self.progress(0, self._total_tasks)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self.failed(exc_val)

    def attach(self, task: Task) -> Task:
        """
        "Attaches" the reporter to a task. Useful for tracking the completion of tasks in a loop that submits tasks to a task pool
        """
        task.add_done_callback(self._increment_progress)
        return task

    def _increment_progress(self, _) -> None:
        # Contention for this should be extremely low, so it shouldn't have much impact on the event loop
        with self._lock:
            self._complete_tasks += 1
            progress = self._complete_tasks

        self.progress(progress, self._total_tasks)
