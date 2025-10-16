from typing import Callable, Dict

from ..soil.event import Event
from .fixed_job import FixedJob


class EventJob(FixedJob):

    def __init__(self, topic: str, interval: int, callback: Callable, event: Event):
        FixedJob.__init__(self, f'events/{topic}', interval, callback)
        self._event = event
        self._last_value = None

    @property
    def type(self) -> str:
        return 'event'

    def _is_triggered(self) -> bool:
        value = self._callback()
        if isinstance(value, tuple):
            assert len(value) == 2
            value, covariance = value

        updated = self._event.is_triggered(value)
        if isinstance(updated, list):
            updated = any(updated)
        return updated

    def data(self, model: Dict = None) -> Dict:
        self._event.trigger(self._last_value)
        return self._event.serialize()
