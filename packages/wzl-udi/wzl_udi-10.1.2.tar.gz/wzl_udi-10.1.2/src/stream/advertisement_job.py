from typing import Dict, Tuple, Any

import rdflib

from .fixed_job import FixedJob
from .job import JobError
from ..soil.component import Component
from ..utils.resources import ResourceType


class AdvertisementJob(FixedJob):

    def __init__(self, topic: str):
        FixedJob.__init__(self, topic, 60, None)

    @property
    def type(self) -> str:
        return 'component'

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, value: int):
        self._interval = value
        self.schedule()

    @property
    def value(self) -> Tuple[Any, Any]:
        return None

    def data(self, model: Component = None) -> Dict:
        if model is None:
            raise JobError('Can not retrieve data. Model is missing')
        try:
            uuids = self.topic.split('/')
            data = model.__getitem__(uuids).serialize(['all'], False)

            return data
        except Exception as e:
            raise JobError('Can not retrieve data. Due to another error.', predeccessor=e)

    def semantic_data(self, model: Component = None) -> (str, rdflib.Graph):
        if model is None:
            raise JobError('Can not retrieve semantic data. Model is missing')
        try:
            uuids = self.topic.split('/')
            element = model.__getitem__(uuids)

            data = element.serialize_semantics(ResourceType.metadata, recursive=True)

            return element.semantic_name, data
        except Exception as e:
            raise JobError('Can not semantic retrieve data. Due to another error.', predeccessor=e)
