import collections

from flask import Flask, request, make_response
from spylogger import get_logger

from protonpack.core import ProtonPack, Event
from protonpack.core.subscribe import SubscriberManager, Subscriber
from protonpack.core.utils import json_dumps


app = Flask(__name__)
app.logger = get_logger()


@app.route("/", methods=['GET', 'POST'])
def root_handler():
    if request.method == "POST":
        data = request.get_json(force=True)
        app.logger.info(json_dumps(data))
    return make_response(json_dumps({"status": "ok"}), 200)


@app.route("/streams", methods=['GET'])
def get_streams():
    streams = ProtonPack.list_streams()
    return make_response(json_dumps({"status": "ok", "streams": list(streams)}), 200)


@app.route("/streams/<stream>", methods=['GET', 'POST'])
def get_stream_info(stream):
    if request.method == "GET":
        info = ProtonPack.stream_info(stream)
        return make_response(json_dumps({"status": "ok", "stream": stream, "info": info}), 200)
    elif request.method == "POST":
        raw = request.get_json(force=True)
        if isinstance(raw, collections.Mapping):
            event = Event.from_dict(raw)
            evt_id = ProtonPack.send_event(stream, event)
            raw["event_id"] = evt_id
            app.logger.debug({"action": "event_posted", "event": raw})
            return make_response(json_dumps({"status": "ok", "stream": stream, "events": [evt_id]}), 200)
        else:
            evt_ids = []
            for evt in raw:
                event = Event.from_dict(evt)
                evt_id = ProtonPack.send_event(stream, event)
                evt["event_id"] = evt_id
                evt_ids.append(evt_id)
                app.logger.debug({"action": "event_posted", "event": evt})
            return make_response(json_dumps({"status": "ok", "stream": stream, "events": evt_ids}), 200)


@app.route("/streams/<stream>/groups", methods=['GET'])
def get_stream_consumer_groups(stream):
    groups = ProtonPack.list_consumer_groups(stream)
    return make_response(json_dumps({"status": "ok", "stream": stream, "groups": [group.to_dict() for group in groups]}), 200)


@app.route("/streams/<stream>/groups", methods=['POST'])
def put_stream_consumer_group(stream):
    data = request.get_json(force=True)
    group_name = data.get("group_name")
    group = ProtonPack.create_consumer_group(stream, group_name)
    return make_response(json_dumps({"status": "ok", "stream": stream, "group_name": group_name, "created": group}), 200)


@app.route("/streams/<stream>/subscribers", methods=['GET'])
def get_stream_subscribers(stream):
    subscribers = SubscriberManager.get_subscribers_for(stream)
    return make_response(json_dumps({"status": "ok", "stream": stream, "subscribers": [subscriber.to_dict() for subscriber in subscribers]}), 200)


@app.route("/streams/<stream>/subscribers", methods=['POST'])
def put_stream_subscriber(stream):
    data = request.get_json(force=True)
    subscriber = Subscriber.from_dict(data)
    created = SubscriberManager.put_subscriber(subscriber)
    return make_response(json_dumps({"status": "ok", "stream": stream, "subscriber": subscriber.subscriber_name, "created": created}), 200)


@app.route("/streams/<stream>/subscribers/<subscriber_name>", methods=['DELETE'])
def delete_stream_subscriber(stream, subscriber_name):
    ok = False
    subscribers = SubscriberManager.get_subscribers_for(stream)
    for subscriber in subscribers:
        if subscriber.subscriber_name == subscriber_name:
            ok = SubscriberManager.del_subscriber(subscriber)
            break
    return make_response(json_dumps({"status": "ok", "stream": stream, "subscriber": subscriber_name, "deleted": ok}), 200)
