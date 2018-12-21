from enum import Enum
import json
from typing import List, Dict
from uuid import uuid4

import requests

from .base import BaseManager
from . import Event


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

    def handle_event(self, event: Event, consumer_group: str, consumer_id: str) -> bool:
        # test for topic match
        if self.topics and "*" not in self.topics:
            if event.topic not in self.topics:
                return False

        # test for evt_types match
        if self.evt_types and "*" not in self.evt_types:
            if event.evt_type not in self.evt_types:
                return False

        # test for activities match
        if self.activities and "*" not in self.activities:
            if event.activity not in self.activities:
                return False

        # if we got this far then we matched all the criteria
        payload = {
            "stream": self.stream,
            "event": event.to_dict(),
            "consumer_group": consumer_group,
            "consumer_id": consumer_id,
            "subscriber_name": self.subscriber_name,
        }

        if self.protocol == Protocol.HTTP:
            response = requests.post(self.endpoint, json=payload)
            if response.status_code == 200:
                return True
            else:
                # TODO - better logging, retry strategies, failure modes
                print("---- bad response ----")
                print(response.text)
                print("----------------------")
                return False
        elif self.protocol == Protocol.GRPC:
            # TODO
            pass
        return True

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
