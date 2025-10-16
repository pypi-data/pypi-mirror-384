from typing import Callable

from .job import Job


class FixedJob(Job):

    def __init__(self, topic: str, interval: float, callback: Callable):
        Job.__init__(self, topic, callback)
        self._interval = interval
        self.schedule()

    @property
    def interval(self) -> float:
        return self._interval

    def _is_triggered(self) -> bool:
        return True
