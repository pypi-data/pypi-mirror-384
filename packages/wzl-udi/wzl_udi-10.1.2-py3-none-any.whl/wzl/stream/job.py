import datetime
from abc import ABC, abstractmethod
from typing import Callable, Any, Dict, Tuple

import rdflib

from ..soil import variable
from ..soil.component import Component
from ..soil.semantics import Namespaces
from ..utils.resources import ResourceType


class JobError(Exception):

    def __init__(self, message: str, predeccessor: Exception = None):
        self._predecessor: predeccessor
        self._message = message

    @property
    def message(self) -> str:
        return self._message


class Job(ABC):
    """Abstract base class for all jobs containing the basic information for continuous automatic data streaming.

    Attributes:
        topic: The topic to which a message should be published, if the job is triggered.
        callback: Method to be called if the job is triggered to retrieve the value to be published.
        next: Point in time (future) at which the job has to be checked again.

    """

    def __init__(self, topic: str, callback: Callable):
        """Constructor

        Args:
            topic: The topic as used in a publish/subscribe-protocol under the which the data is published.
            callback: A method called if the job is triggered to retrieve the value to be published.
            next: Point in time (future) at which the job has to be checked again.
        """
        self._topic = topic
        self._callback = callback
        self._next = datetime.datetime.now()

    @property
    def type(self) -> str:
        return 'measurement'

    @property
    def topic(self) -> str:
        return self._topic

    @property
    @abstractmethod
    def interval(self) -> float:
        ...

    @property
    def value(self) -> Tuple[Any, Any]:
        """

        Returns: the value together with the covariance, which might None

        """
        return self._callback()

    def is_triggered(self, time: datetime.datetime = None) -> bool:
        try:
            time = time if time is not None else datetime.datetime.now()
            return self._next is not None and self._next <= time and self._is_triggered()
        except Exception as e:
            raise JobError('is_triggered failed', predeccessor=e)

    @abstractmethod
    def _is_triggered(self) -> bool:
        ...

    def determine_next(self, time: datetime.datetime) -> datetime.datetime:
        if time is None or (self._next is not None and self._next < time):
            return self._next
        else:
            return time

    def start(self) -> None:
        self._next = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)

    def schedule(self) -> None:
        if self._next is not None:
            self.start()

    def stop(self) -> None:
        self._next = None

    def data(self, model: Component = None) -> Dict:
        if model is None:
            raise JobError('Can not retrieve data. Model is missing')
        try:
            uuids = self.topic.split('/')
            data = model.__getitem__(uuids).serialize([], False)

            value, covariance = self.value
            data['uuid'] = self.topic
            data['value'] = value
            data['covariance'] = covariance
            data['timestamp'] = variable.serialize_time(datetime.datetime.now())
            return data
        except Exception as e:
            raise JobError('Can not retrieve data. Due to another error.', predeccessor=e)

    def semantic_data(self, model: Component = None) -> (str, rdflib.Graph):
        if model is None:
            raise JobError('Can not retrieve semantic data. Model is missing')
        try:
            uuids = self.topic.split('/')
            element = model.__getitem__(uuids)
            data = element.serialize_semantics(ResourceType.data)
            data += element.serialize_semantics(ResourceType.uncertainty)
            data += element.serialize_semantics(ResourceType.observation)

            measurement_subject = \
                list((data.subjects(predicate=Namespaces.rdf.type, object=Namespaces.sosa.Observation)))[0]

            # replace value
            data.remove((None, Namespaces.qudt.value, None))
            value, covariance = self.value
            data.add((measurement_subject, Namespaces.qudt.value, element.serialize_value(data, value)))

            # replace timestamp
            data.remove((None, Namespaces.schema.dateCreated, None))
            data.add((measurement_subject, Namespaces.schema.dateCreated, rdflib.Literal(datetime.datetime.now())))

            return element.semantic_name, data
        except Exception as e:
            raise JobError('Can not semantic retrieve data. Due to another error.', predeccessor=e)
