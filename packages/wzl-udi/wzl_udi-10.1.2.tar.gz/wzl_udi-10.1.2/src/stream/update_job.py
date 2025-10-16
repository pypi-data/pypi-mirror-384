from typing import Callable, Tuple, Any

from .fixed_job import FixedJob


class UpdateJob(FixedJob):

    def __init__(self, topic: str, callback: Callable):
        FixedJob.__init__(self, topic, 0.01, callback)
        self._last_value = None
        self._last_covariance = None

    def _is_triggered(self) -> bool:
        value, covariance = self._callback()
        updated = self._last_value != value
        self._last_value = value
        self._last_covariance = covariance
        if isinstance(updated, list):
            updated = any(updated)
        return updated

    @property
    def value(self) -> Tuple[Any, Any]:
        return self._last_value, self._last_covariance
