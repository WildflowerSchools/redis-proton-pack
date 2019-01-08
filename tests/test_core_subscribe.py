import json
from uuid import uuid4

import httpretty

from protonpack.core import Event
from protonpack.core.subscribe import SubscriberManager, Subscriber, Protocol
from .test_utils import RedisRunnerContext


def test_create_and_list_streams():
    with RedisRunnerContext():
        subs = SubscriberManager.list_subscribers()
        existing_len = len(subs)
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
        assert ok is True
        subs = SubscriberManager.list_subscribers()
        assert existing_len + 1 == len(subs)
        this_one = None
        for sub in subs:
            if sub.subscriber_name == subscriber.subscriber_name:
                this_one = sub
                break
        assert this_one is not None
        print(this_one.to_dict())
        print(subscriber.to_dict())
        assert this_one.stream == subscriber.stream
        assert this_one.subscriber_name == subscriber.subscriber_name
        assert set(this_one.topics) == set(subscriber.topics)
        assert set(this_one.evt_types) == set(subscriber.evt_types)
        assert set(this_one.activities) == set(subscriber.activities)
        assert this_one.protocol == subscriber.protocol
        assert this_one.endpoint == subscriber.endpoint
        assert this_one == subscriber


def test_del_subscriber():
    with RedisRunnerContext():
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
        assert ok is True
        subs = SubscriberManager.list_subscribers()
        assert len(subs) == 1
        for sub in subs:
            SubscriberManager.del_subscriber(sub)
        subs = SubscriberManager.list_subscribers()
        assert len(subs) == 0


@httpretty.activate
def test_handle_event():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com",
        body='{"origin": "127.0.0.1"}'
    )
    with RedisRunnerContext():
        subscriber = Subscriber(
            stream=uuid4().hex,
            subscriber_name=uuid4().hex,
            topics=["system"],
            evt_types=["SYS"],
            activities=["init", "verb"],
            protocol=Protocol.HTTP,
            endpoint="http://example.com"
        )
        event = Event(
            event_id="test-event-",
            topic="system",
            evt_type="SYS",
            activity="init",
            ref_id="00",
        )
        ok = subscriber.handle_event(event, "consumer_group", "consumer_id")
        assert ok
        called = httpretty.last_request()
        body = json.loads(called.body)
        assert body["stream"] == subscriber.stream
        assert body["event"]["event_id"] == event.event_id
        assert body["event"]["topic"] == event.topic
        assert body["event"]["evt_type"] == event.evt_type
        assert body["event"]["activity"] == event.activity
        assert body["event"]["ref_id"] == event.ref_id
        assert body["consumer_group"] == "consumer_group"
        assert body["consumer_id"] == "consumer_id"
        assert body["subscriber_name"] == subscriber.subscriber_name


@httpretty.activate
def test_handle_event_mismatch_topic():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com",
        body='{"origin": "127.0.0.1"}'
    )
    with RedisRunnerContext():
        subscriber = Subscriber(
            stream=uuid4().hex,
            subscriber_name=uuid4().hex,
            topics=["system"],
            evt_types=["SYS"],
            activities=["init", "verb"],
            protocol=Protocol.HTTP,
            endpoint="http://example.com"
        )
        event = Event(
            event_id="test-event-",
            topic="jazz",
            evt_type="SYS",
            activity="init",
            ref_id="00",
        )
        ok = subscriber.matches(event)
        assert ok is False
        assert httpretty.has_request() is False


@httpretty.activate
def test_handle_event_mismatch_evt_type():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com",
        body='{"origin": "127.0.0.1"}'
    )
    with RedisRunnerContext():
        subscriber = Subscriber(
            stream=uuid4().hex,
            subscriber_name=uuid4().hex,
            topics=["system"],
            evt_types=["SYS"],
            activities=["init", "verb"],
            protocol=Protocol.HTTP,
            endpoint="http://example.com"
        )
        event = Event(
            event_id="test-event-",
            topic="system",
            evt_type="BOM",
            activity="init",
            ref_id="00",
        )
        ok = subscriber.matches(event)
        assert ok is False
        assert httpretty.has_request() is False


@httpretty.activate
def test_handle_event_mismatch_activities():
    httpretty.register_uri(
        httpretty.POST,
        "http://example.com"
    )
    with RedisRunnerContext():
        subscriber = Subscriber(
            stream=uuid4().hex,
            subscriber_name=uuid4().hex,
            topics=["system"],
            evt_types=["SYS"],
            activities=["init", "verb"],
            protocol=Protocol.HTTP,
            endpoint="http://example.com"
        )
        event = Event(
            event_id="test-event-",
            topic="system",
            evt_type="SYS",
            activity="write",
            ref_id="00",
        )
        ok = subscriber.matches(event)
        assert ok is False
        assert httpretty.has_request() is False
