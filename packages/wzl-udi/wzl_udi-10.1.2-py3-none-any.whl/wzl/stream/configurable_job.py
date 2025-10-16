from typing import Callable, Union

from .job import Job


class ConfigurableJob(Job):
    """
    Works exactly as a Job, despite interval is a callable which returns an integer value, used for determining delay between two job executions.
    """

    def __init__(self, topic: str, interval: Callable, callback: Callable):
        Job.__init__(self, topic, callback)
        self._interval = interval
        self.schedule()

    @property
    def interval(self) -> Union[int, float]:
        return self._interval()

    def _is_triggered(self) -> bool:
        return True
