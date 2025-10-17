import logging

from libqcanvas.task_master.task_id import TaskID
from libqcanvas.task_master.task_master import Reporter, TaskMaster

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class _DefaultTaskMaster(TaskMaster):
    def report_failed(self, _task_id: TaskID, context: str | Exception) -> None:
        _logger.warning("Task %s failed - %s", _task_id, context)

    def report_progress(self, _task_id: TaskID, current: int, total: int) -> None:
        if current == total:
            if total == 0:
                _logger.info("Task %s - ?%%", _task_id)
            else:
                _logger.info("Task %s - finished", _task_id)
        else:
            _logger.info(
                "Task %s progress: %s%%", _task_id, f"{(current / total) * 100:.2f}"
            )


_global_task_master = _DefaultTaskMaster()


def get_global_task_master() -> TaskMaster:
    global _global_task_master
    return _global_task_master


def set_global_task_master(new_task_master: TaskMaster) -> None:
    global _global_task_master
    _global_task_master = new_task_master


def register_reporter[T: Reporter](reporter: T) -> T:
    return _global_task_master.accept(reporter)
