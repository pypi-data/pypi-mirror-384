import datetime
import json
import traceback
from typing import List

from wzl.mqtt import MQTTPublisher
from wzl.mqtt.exceptions import ClientNotFoundError

from .advertisement_job import AdvertisementJob
from .job import Job, JobError
from ..soil.component import Component
from ..utils import root_logger
from ..utils import serialize

logger = root_logger.get(__name__)


class StreamScheduler(object):
    """Processes Jobs and published messages if, certain conditions are met.

    Periodically, checks the status of scheduled jobs. If a job is triggered, it publishes a message via all publishers handed to the scheduler.
    """

    def __init__(self, loop, schedule: List[Job], publisher: MQTTPublisher = None,
                 start_immediately: bool = False, dataformat: str = 'json', model: 'Component' = None, advertise: int = 10, semantic: bool = False):
        """Constructor.

        Args:
            loop:
            schedule: List of jobs scheduled be checked regularly.
            publishers: List of MQTT publishers, which are used to publish a message if a job is triggered.
            start_immediately: If True, the all jobs are scheduled immediately, i.e. the update method is called checking the jobs.
        """
        if dataformat not in ['json', 'xml']:
            raise ValueError('Dataformat must be one of "json" or "xml".')

        self._loop = loop
        self._schedule: List[Job] = schedule
        self._publisher: MQTTPublisher = publisher if publisher is not None else []
        self._running: bool = start_immediately
        self._dataformat: str = dataformat
        self._model: Component = model
        self._advertise = advertise
        self._semantic = semantic
        
        for job in schedule:
            if isinstance(job, AdvertisementJob):
                if self._advertise > 0:
                    job.interval = self._advertise
                else:
                    job.stop()

        if start_immediately:
            self._update()

    def start(self) -> None:
        """Schedules all jobs stored in the attribute _schedule.

        """
        self._running = True
        self._update()

    def stop(self) -> None:
        """Stops scheduling and processing of jobs.

        """
        self._running = False

    def add_jobs(self, schedule: List[Job]):
        self._schedule += schedule
        for job in schedule:
            if isinstance(job, AdvertisementJob):
                if self._advertise > 0:
                    job.interval = self._advertise
                else:
                    job.stop()


    def remove_jobs(self, fqid: str):
        jobs_to_remove = []
        for job in self._schedule:
            if fqid in job.topic:
                jobs_to_remove += [jobs_to_remove]
        for job in jobs_to_remove:
            self._schedule.remove(job)

    def _update(self) -> None:
        """Processes all scheduled jobs.

        Method calls itself infinitely, until stop() is called.
        Checks for all jobs, if it is triggered, and publishes messages, if triggered.
        Computes the interval to the next due job, and schedules the call of _update accordingly.

        Returns:

        """
        if self._running:
            next = None
            now = datetime.datetime.now()
            for job in self._schedule:
                try:
                    if job.is_triggered(now):
                        # send syntactic data package
                        if self._dataformat == 'json':
                            message = json.dumps(job.data(self._model))
                        elif self._dataformat == 'xml':
                            message = serialize.to_xml(job.type, job.data(self._model))

                        try:
                            self._publisher.get('tier1').publish(job.topic, message, 1)
                        except ClientNotFoundError:
                            logger.warn('Client not found error occured.')
                            logger.warn(traceback.format_exc())
                            self._publisher.publish(job.topic, message, 1)

                        # try to send semantic data package
                        if self._semantic:
                            try:
                                url, semantic_data = job.semantic_data(self._model)
                                url = url.replace('https://', '').replace('http://', '')
                                if self._dataformat == 'json':
                                    message = semantic_data.serialize(format='json-ld')
                                elif self._dataformat == 'xml':
                                    message = semantic_data.serialize(format='xml')

                                try:
                                    self._publisher.get('tier2').publish(url, message, 1)
                                except ClientNotFoundError:
                                    logger.warn('Client not found error occured.')
                                    logger.warn(traceback.format_exc())
                                    self._publisher.publish(url, message, 1)

                            except JobError as e:
                                logger.error(e.message)
                                logger.error(traceback.format_exc())

                        job.schedule()
                    next = job.determine_next(next)
                except JobError as e:
                    logger.error(e.message)
                    logger.error(traceback.format_exc())
                    pass

            if next is None:
                next = now + datetime.timedelta(seconds=10)
            elif next < now:
                next = now

            self._loop.call_later((next - now).seconds + (next - now).microseconds / 1e6, self._update)
