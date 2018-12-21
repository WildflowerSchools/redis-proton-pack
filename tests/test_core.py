from uuid import uuid4

import pytest

from protonpack.core import Event, ProtonPack
from .test_utils import RedisRunnerContext


def test_list_streams():
    with RedisRunnerContext():
        streams = ProtonPack.list_streams()
        assert streams is not None
        assert isinstance(streams, set)
        test_stream_name = uuid4().hex
        stream_count = len(streams)
        ProtonPack.create_stream(test_stream_name)
        streams = ProtonPack.list_streams()
        assert len(streams) == stream_count + 1


def test_stream_exists():
    with RedisRunnerContext():
        test_stream_name = uuid4().hex
        assert not ProtonPack.stream_exists(test_stream_name)
        ProtonPack.create_stream(test_stream_name)
        assert ProtonPack.stream_exists(test_stream_name)


def test_send_event():
    with RedisRunnerContext():
        client = ProtonPack.redis_connect()
        test_stream_name = uuid4().hex
        ProtonPack.create_stream(test_stream_name)
        length = client.xlen(test_stream_name)
        assert length == 1
        evt = Event(topic="test", evt_type="TEST", activity="test_send_event")
        ProtonPack.send_event(test_stream_name, evt)
        length = client.xlen(test_stream_name)
        assert length == 2


def test_invalid_key():
    with RedisRunnerContext():
        client = ProtonPack.redis_connect()
        test_stream_name = uuid4().hex
        client.set(test_stream_name, "ima-lima-bean")
        with pytest.raises(Exception, match="invalid stream key"):
            ProtonPack.create_stream(test_stream_name)


def test_list_consumer_groups_and_create_consumer_group():
    with RedisRunnerContext():
        test_stream_name = uuid4().hex
        ProtonPack.create_stream(test_stream_name)
        groups = ProtonPack.list_consumer_groups(test_stream_name)
        assert len(groups) == 0
        ProtonPack.create_consumer_group(test_stream_name, "consumers_1")
        groups = ProtonPack.list_consumer_groups(test_stream_name)
        assert len(groups) == 1
        assert "consumers_1" in [group.name for group in groups]
        ProtonPack.create_consumer_group(test_stream_name, "consumers_2")
        groups = ProtonPack.list_consumer_groups(test_stream_name)
        assert len(groups) == 2
        assert "consumers_2" in [group.name for group in groups]


def test_list_consumer_groups_create_if():
    with RedisRunnerContext():
        test_stream_name = uuid4().hex
        streams = ProtonPack.list_streams()
        assert test_stream_name not in streams
        groups = ProtonPack.list_consumer_groups(test_stream_name, True)
        assert len(groups) == 0
        streams = ProtonPack.list_streams()
        assert test_stream_name in streams


def test_create_consumer_group():
    with RedisRunnerContext():
        test_stream_name = uuid4().hex
        streams = ProtonPack.list_streams()
        assert test_stream_name not in streams
        grp = ProtonPack.create_consumer_group(test_stream_name, "group")
        assert grp
        streams = ProtonPack.list_streams()
        assert test_stream_name in streams


def test_acknowledge_events():
    with RedisRunnerContext():
        groupname = "group"
        consumername = "consumer"
        test_stream_name = uuid4().hex
        evt = Event(topic="test", evt_type="TEST", activity="test_send_event")
        evt_id = ProtonPack.send_event(test_stream_name, evt)
        assert evt_id is not None
        ProtonPack.create_consumer_group(test_stream_name, groupname)
        ProtonPack.poll_events(test_stream_name, groupname, consumername, 100, 10000)
        ack = ProtonPack.acknowledge_events(test_stream_name, groupname, evt_id)
        assert ack == 1


def test_event_dicts():
    evt = Event(event_id="event_id", topic="topic", evt_type="evt_type", activity="activity", timestamp="timestamp", ref_id="ref_id")
    assert "event_id" == evt.event_id
    assert "topic" == evt.topic
    assert "evt_type" == evt.evt_type
    assert "activity" == evt.activity
    assert "timestamp" == evt.timestamp
    assert "ref_id" == evt.ref_id

    dict_evt = evt.to_dict()

    assert "event_id" == dict_evt.get("event_id")
    assert "topic" == dict_evt.get("topic")
    assert "evt_type" == dict_evt.get("evt_type")
    assert "activity" == dict_evt.get("activity")
    assert "timestamp" == dict_evt.get("timestamp")
    assert "ref_id" == dict_evt.get("ref_id")

    from_dict_evt = Event.from_dict(dict_evt)
    assert "event_id" == from_dict_evt.event_id
    assert "topic" == from_dict_evt.topic
    assert "evt_type" == from_dict_evt.evt_type
    assert "activity" == from_dict_evt.activity
    assert "timestamp" == from_dict_evt.timestamp
    assert "ref_id" == from_dict_evt.ref_id
