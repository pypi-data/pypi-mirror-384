from abc import ABC, abstractmethod


class CanvasSyncObserver(ABC):
    """
    A CanvasSyncObserver subscribes to events related to synchronisation from canvas
    """

    @abstractmethod
    def new_content_found(self, content: object): ...


class CanvasSyncObservable:
    """
    A CanvasSyncObservable publishes events related to synchronisation from canvas
    """

    def __init__(self):
        self._observers: list[CanvasSyncObserver] = []

    def notify_observers_for_updated_item(self, content: object):
        for observer in self._observers:
            observer.new_content_found(content)

    @property
    def observers(self) -> list[CanvasSyncObserver]:
        return self._observers
