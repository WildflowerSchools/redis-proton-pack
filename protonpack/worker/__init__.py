import time
from uuid import uuid4

from spylogger import get_logger

from protonpack.core import ProtonPack
from protonpack.core.subscribe import SubscriberManager
from protonpack.core.base import BaseManager
from protonpack.core.utils import json_dumps


logger = get_logger()


class GhostBuster(BaseManager):

    def __init__(self, stream_name: str, consumer_group: str, consumer_id: str=None, janitor: bool=False, batch_size: int=10, block_time: int=1000):
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_id = consumer_id or uuid4().hex
        self.batch_size = batch_size
        self.block_time = block_time
        self.janitor = janitor
        self.log(action="worker_init")
        ProtonPack.create_consumer_group(stream_name, consumer_group)

    def log(self, **kwargs):
        msg = {
            "message": f"GhostBuster",
            "consumer": self.consumer_group,
            "consumerid": self.consumer_id,
            "stream": self.stream_name,
            "batch_size": self.batch_size,
            "block_time": self.block_time,
            "janitor": self.janitor,
        }
        msg.update(kwargs)
        logger.debug(msg)

    def start(self, forever=True):
        self.log(action="worker_start")
        while True:
            if self.janitor:
                self.janitorial()
            for x in range(0, 3):
                self.do_poll()
                time.sleep(2)
            if not forever:
                return

    def do_poll(self):
        batch = ProtonPack.poll_events(self.stream_name, self.consumer_group, self.consumer_id, self.batch_size, self.block_time)
        self.log(action="worker_batch", batch_len=len(batch))
        for item in batch:
            if self.handle_event(item):
                ProtonPack.acknowledge_events(self.stream_name, self.consumer_group, item.event_id)

    def janitorial(self):
        """ TODO
        Idea here is to check to make sure the pending list is clear for this consumer and to check
        for pending items that are old and claim them to be processed by this consumer. It is best that
        not every worker is a janitor.
        """
        pass

    def queue_for_subscriber_error(self, subscriber, evt):
        client = self.redis_connect()
        return client.xadd(f"janitorial::{self.stream_name}", {"subscriber": subscriber, "event": json_dumps(evt)})

    def handle_event(self, event) -> bool:
        """
        loads list of subscribers, which should get cached for a short time - TODO ttl cache of subscribers list
        loops over the subscribers, which each have auto-retry
        tracks the status
        returns True when any of the subscribers are ok
        returns False only when all fail
        """
        subscribers = SubscriberManager.get_subscribers_for(self.stream_name)
        evt = event.to_dict()
        self.log(action="handle_event", subscribers=len(subscribers), event=evt)
        responses = []
        for subscriber in subscribers:
            ok = subscriber.handle_event(event, self.consumer_group, self.consumer_id)
            responses.append(ok)
            if not ok:
                self.log(action="subscriber_fail", subscriber=subscriber.to_dict(), event=evt)
                self.queue_for_subscriber_error(subscriber.subscriber_name, evt)
        return any(responses)
