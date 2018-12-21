from uuid import uuid4
from protonpack.core import ProtonPack
from protonpack.core.subscribe import SubscriberManager


class GhostBuster(object):

    def __init__(self, stream_name: str, comsumer_group: str, consumer_id: str=None, janitor: bool=False, batch_size: int=10, block_time: int=1000):
        self.stream_name = stream_name
        self.comsumer_group = comsumer_group
        self.consumer_id = consumer_id or uuid4().hex
        self.batch_size = batch_size
        self.block_time = block_time
        self.janitor = janitor
        print(stream_name)
        print(comsumer_group)
        ProtonPack.create_consumer_group(stream_name, comsumer_group)

    def start(self):
        while True:
            if self.janitor:
                self.janitorial()
            for x in range(0, 10):
                self.do_poll()

    def do_poll(self):
        batch = ProtonPack.poll_events(self.stream_name, self.consumer_group, self.consumer_id, self.batch_size, self.block_time)
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

    def handle_event(self, event) -> bool:
        subscribers = SubscriberManager.get_subscribers_for(self.stream_name)
        for subscriber in subscribers:
            ok = subscriber.handle_event(event, self.consumer_group, self.consumer_id)
            if not ok:
                print(f"event {event.event_id} failed for {subscriber.subscriber_name}")
        return True
