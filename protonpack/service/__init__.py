import logging

from flask import Flask, request, make_response

from protonpack.core import ProtonPack
from protonpack.core.subscribe import SubscriberManager, Subscriber
from protonpack.core.utils import json_dumps


app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def root_handler():
    if request.method == "POST":
        data = request.get_json(force=True)
        logging.info(json_dumps(data))
    return make_response(json_dumps({"status": "ok"}), 200)


@app.route("/streams", methods=['GET'])
def get_streams():
    streams = ProtonPack.list_streams()
    return make_response(json_dumps({"status": "ok", "streams": list(streams)}), 200)


@app.route("/streams/<stream>", methods=['GET'])
def get_stream_info(stream):
    info = ProtonPack.stream_info(stream)
    return make_response(json_dumps({"status": "ok", "stream": stream, "info": info}), 200)


@app.route("/streams/<stream>/groups", methods=['GET'])
def get_stream_consumer_groups(stream):
    groups = ProtonPack.list_consumer_groups(stream)
    return make_response(json_dumps({"status": "ok", "stream": stream, "groups": [group.to_dict() for group in groups]}), 200)


@app.route("/streams/<stream>/groups", methods=['POST'])
def put_stream_consumer_group(stream):
    data = request.get_json(force=True)
    logging.info(json_dumps(data))
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
    logging.info(json_dumps(data))
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
