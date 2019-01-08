import json
import time
from uuid import uuid4

# import pytest
import httpretty

from protonpack.core import Event, ProtonPack
from protonpack.core.subscribe import Subscriber, SubscriberManager, Protocol
from protonpack.worker import GhostBuster

from .test_utils import RedisRunnerContext



@httpretty.activate
def test_workers_unite():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com",
        body='{"origin": "127.0.0.1"}',
        status=200,

    )
    with RedisRunnerContext():
        # -- create a subscriber that is mocked with httpretty
        subscriber = Subscriber(
            stream=uuid4().hex,
            subscriber_name=uuid4().hex,
            topics=["system"],
            evt_types=["SYS"],
            activities=["init", "verb"],
            protocol=Protocol.HTTP,
            endpoint="http://example.com"
        )
        ok = SubscriberManager.put_subscriber(subscriber)
        assert ok

        # -- prepare an event to send
        event = Event(
            topic="system",
            evt_type="SYS",
            activity="init",
            ref_id="00",
        )
        ok = ProtonPack.send_event(subscriber.stream, event)
        assert ok

        # -- start up a worker and have it consume the stream
        gb = GhostBuster(subscriber.stream, "consumer_group", "consumer_id")
        gb.start(False)

        # -- assert the handler uri is called
        called = httpretty.last_request()
        print(dir(called))
        assert called.body is not None
        assert called.body != ""
        body = json.loads(called.body)
        assert body["stream"] == subscriber.stream
        assert body["event"]["topic"] == event.topic
        assert body["event"]["evt_type"] == event.evt_type
        assert body["event"]["activity"] == event.activity
        assert body["event"]["ref_id"] == event.ref_id
        assert body["consumer_group"] == "consumer_group"
        assert body["consumer_id"] == "consumer_id"
        assert body["subscriber_name"] == subscriber.subscriber_name
