import asyncio
from asyncio import Task


class CollectingTaskGroup[T](asyncio.TaskGroup):
    def __init__(self):
        super().__init__()
        self._preserved_tasks = []
        self._results = []

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

        self._results = [task.result() for task in self._preserved_tasks if task.done()]
        self._preserved_tasks.clear()

    def create_task(self, coro, *, name=None, context=None) -> Task:
        result = super().create_task(coro, name=name, context=context)
        self._preserved_tasks.append(result)
        return result

    @property
    def results(self) -> list[T]:
        return self._results
