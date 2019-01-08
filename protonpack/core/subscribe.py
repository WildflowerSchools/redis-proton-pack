from enum import Enum
import json
from typing import List, Dict
import time
from uuid import uuid4

import requests
from retrying import retry
from spylogger import get_logger

from .base import BaseManager
from . import Event


logger = get_logger()


class Protocol(Enum):
    HTTP = "HTTP"
    GRPC = "GRPC"


class Subscriber(object):

    def __init__(self,
                 stream: str,
                 subscriber_name: str=None,
                 topics: List[str]=None,
                 evt_types: List[str]=None,
                 activities: List[str]=None,
                 protocol: Protocol=Protocol.HTTP,
                 endpoint: str=None):
        self.stream = stream
        self.subscriber_name = subscriber_name or uuid4()
        self.topics = topics
        self.evt_types = evt_types
        self.activities = activities
        self.protocol = protocol
        self.endpoint = endpoint

    def __eq__(self, other: 'Subscriber') -> bool:
        if other is not None:
            return self.stream == other.stream and \
                self.subscriber_name == other.subscriber_name and \
                set(self.topics) == set(other.topics) and \
                set(self.evt_types) == set(other.evt_types) and \
                set(self.activities) == set(other.activities) and \
                self.protocol == other.protocol and \
                self.endpoint == other.endpoint
        return False

    def to_dict(self) -> Dict:
        obj = dict()
        for key in ["stream", "subscriber_name", "topics", "activities", "protocol", "endpoint", "evt_types"]:
            value = getattr(self, key)
            if value:
                obj[key] = value
        obj["protocol"] = self.protocol.value
        return obj

    def list_key(self):
        return "pp-subscriptions-{stream}".format(stream=self.stream)

    def matches(self, event: Event) -> bool:
        # test for topic match
        if self.topics and "*" not in self.topics:
            if event.topic not in self.topics:
                self.log(action="handle_event_nomatch_topic", event_id=event.event_id, topic=event.topic)
                return False

        # test for evt_types match
        if self.evt_types and "*" not in self.evt_types:
            if event.evt_type not in self.evt_types:
                self.log(action="handle_event_nomatch_evt_types", event_id=event.event_id)
                return False

        # test for activities match
        if self.activities and "*" not in self.activities:
            if event.activity not in self.activities:
                self.log(action="handle_event_nomatch_activity", event_id=event.event_id)
                return False
        return True

    def handle_event(self, event: Event, consumer_group: str, consumer_id: str) -> bool:
        if not self.matches(event):
            return True

        # if we got this far then we matched all the criteria
        payload = {
            "stream": self.stream,
            "event": event.to_dict(),
            "consumer_group": consumer_group,
            "consumer_id": consumer_id,
            "subscriber_name": self.subscriber_name,
        }
        self.log(action="handle_event_match", event_id=event.event_id)

        if self.protocol == Protocol.HTTP:
            @retry(stop_max_attempt_number=10, wait_exponential_multiplier=100)
            def __make_request():
                response = requests.post(self.endpoint, json=payload)
                if response.status_code >= 200 and response.status_code < 300:
                    return True
                else:
                    self.log(error=True, action="handle_event_invalid_status", status_code=response.status_code)
                    raise Error(f"request failed: {response.status_code}")
            try:
                return __make_request()
            except Error as e:
                self.log(error=True, action="handle_event_failure", event_id=event.event_id)
                return False
        elif self.protocol == Protocol.GRPC:
            # do this because GRPC is not yet supported
            self.log(error=True, action="handle_event_failure", event_id=event.event_id)
            pass
        return True

    def log(self, error=False, **kwargs):
        msg = {
            "message": "Subscriber",
            "stream": self.stream,
            "subscriber_name": self.subscriber_name,
            "topics": self.topics,
            "activities": self.activities,
            "protocol": self.protocol.value,
            "endpoint": self.endpoint,
            "evt_types": self.evt_types,
        }
        msg.update(kwargs)
        if error:
            logger.error(msg)
        else:
            logger.debug(msg)

    @classmethod
    def from_dict(cls, obj) -> 'Subscriber':
        return cls(
            stream=obj.get("stream"),
            subscriber_name=obj.get("subscriber_name"),
            topics=obj.get("topics"),
            activities=obj.get("activities"),
            protocol=Protocol[obj.get("protocol")],
            endpoint=obj.get("endpoint"),
            evt_types=obj.get("evt_types"),
        )


class SubscriberManager(BaseManager):

    @classmethod
    def put_subscriber(cls, subscriber: Subscriber) -> bool:
        client = cls.redis_connect()
        if client.sadd(subscriber.list_key(), json.dumps(subscriber.to_dict())):
            return True
        return False

    @classmethod
    def del_subscriber(cls, subscriber: Subscriber) -> bool:
        client = cls.redis_connect()
        ok = client.srem(subscriber.list_key(), json.dumps(subscriber.to_dict()))
        return ok == 1

    @classmethod
    def get_subscribers_for(cls, stream: str) -> List[Subscriber]:
        print(f'fetching get_subscribers_for {stream}')
        subs = list()
        client = cls.redis_connect()
        key = "pp-subscriptions-{stream}".format(stream=stream)
        for subscriber in client.smembers(key):
            print(subscriber)
            subs.append(Subscriber.from_dict(json.loads(subscriber)))
        return subs

    @classmethod
    def list_subscribers(cls) -> List[Subscriber]:
        subs = list()
        client = cls.redis_connect()
        for key in client.scan_iter(match="pp-subscriptions-*"):
            for sub in cls.get_subscribers_for(key.decode("utf8")[17:]):
                subs.append(sub)
        return subs
