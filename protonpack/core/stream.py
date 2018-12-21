import logging
from typing import List

from redis.exceptions import ResponseError

from .base import BaseManager
from .utils import decode, now


def fix_keys(mapping):
    result = dict()
    for k in mapping.keys():
        result[decode(k)] = mapping[k]
    return result


class Event(object):

    def __init__(self, event_id=None, topic=None, evt_type=None, activity=None, timestamp=None, ref_id=None):
        self.event_id = event_id
        self.topic = topic
        self.evt_type = evt_type
        self.activity = activity
        self.timestamp = timestamp if timestamp else now()
        self.ref_id = ref_id

    def to_dict(self):
        obj = dict()
        for key in ["event_id", "topic", "evt_type", "activity", "timestamp", "ref_id"]:
            value = getattr(self, key)
            if value:
                obj[key] = value
        return obj

    def __str__(self):
        return "<Event %s>" % self.event_id

    @classmethod
    def from_dict(cls, obj):
        return cls(
            event_id=obj.get("event_id"),
            topic=obj.get("topic"),
            evt_type=obj.get("evt_type"),
            activity=obj.get("activity"),
            timestamp=obj.get("timestamp"),
            ref_id=obj.get("ref_id")
        )

    @classmethod
    def parse_group_read(cls, response):
        results = dict()
        for stream in response:
            stream_name = stream[0]
            events = list()
            for record in stream[1]:
                event = cls.parse_evt_record(record)
                events.append(event)
            results[stream_name] = events
        return results

    @classmethod
    def parse_evt_record(cls, record):
        event_id = record[0]
        args = record[1]
        args["event_id"] = event_id
        args = fix_keys(args)
        return Event.from_dict(args)


class ConsumerGroup(object):

    def __init__(self, name, consumers, pending, last_delivered_id):
        self.name = name
        self.consumers = consumers
        self.pending = pending
        self.last_delivered_id = last_delivered_id

    def to_dict(self):
        obj = dict()
        for key in ["name", "consumers", "pending", "last_delivered_id"]:
            value = getattr(self, key)
            obj[key] = value
        return obj

    @classmethod
    def from_redis(cls, obj):
        name = obj.get("name")
        consumers = obj.get("consumers")
        pending = obj.get("pending")
        last_delivered_id = obj.get("last-delivered-id")
        return cls(
            name=decode(name),
            consumers=decode(consumers),
            pending=decode(pending),
            last_delivered_id=decode(last_delivered_id),
        )


class ProtonPack(BaseManager):

    @classmethod
    def send_event(cls, stream: str, evt: Event) -> bool:
        client = cls.redis_connect()
        return client.xadd(stream, evt.to_dict())

    @classmethod
    def list_streams(cls) -> List[str]:
        client = cls.redis_connect()
        streams = set()
        for key in client.keys("*"):
            key_type = client.type(key)
            if key_type == b'stream':
                streams.add(key.decode("utf8"))
        return streams

    @classmethod
    def stream_info(cls, stream: str) -> dict:
        if not cls.stream_exists(stream):
            return {"exists": False}
        client = cls.redis_connect()
        info = client.xinfo_stream(stream)
        logging.error(info)
        for k in info.keys():
            value = info.get(k)
            if k in ["first-entry", "last-entry"]:
                info[k] = Event.parse_evt_record(value)
            else:
                info[k] = value.decode("utf8") if hasattr(value, "decode") else value
        return info

    @classmethod
    def stream_exists(cls, stream: str) -> bool:
        client = cls.redis_connect()
        key_type = client.type(stream)
        if key_type == b'stream':
            return True
        return False

    @classmethod
    def create_stream(cls, stream: str):
        evt = Event(topic="system", evt_type="SYS", activity="init")
        try:
            cls.send_event(stream, evt)
        except ResponseError as err:
            if str(err).startswith("WRONGTYPE"):
                raise Exception("invalid stream key")
            else:
                raise err

    @classmethod
    def list_consumer_groups(cls, stream: str, create_if: bool=False):
        if not cls.stream_exists(stream):
            if create_if:
                cls.create_stream(stream)
            return []
        client = cls.redis_connect()
        groups = client.xinfo_groups(stream)
        groups = [ConsumerGroup.from_redis(grp) for grp in groups]
        return groups

    @classmethod
    def create_consumer_group(cls, stream: str, group_name: str):
        if not cls.stream_exists(stream):
            # streams are created when an event is added to it, so we add a generic "system" event to the stream to force it's creation.
            cls.create_stream(stream)
        client = cls.redis_connect()
        try:
            return client.xgroup_create(stream, group_name, id="0")
        except Exception as err:
            logging.error(err)
            return False

    @classmethod
    def acknowledge_events(cls, stream: str, group_name: str, *msg_ids: List[str]) -> int:
        client = cls.redis_connect()
        return client.xack(stream, group_name, *msg_ids)

    @classmethod
    def poll_events(cls, stream: str, groupname: str, consumername: str, count: int=10, block: int=3000) -> List[Event]:
        client = cls.redis_connect()
        streams = dict()
        streams[stream] = ">"
        results = client.xreadgroup(groupname, consumername, streams, count=count, block=block)
        events = Event.parse_group_read(results)
        return events[stream]
