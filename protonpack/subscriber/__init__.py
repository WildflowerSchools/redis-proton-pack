import json
import logging

from flask import Flask, request, make_response


def echo_subscriber():
    app = Flask(__name__)

    @app.route("", methods=['GET', 'POST'])
    def root_handler():
        if request.method == "POST":
            data = request.get_json(force=True)
            logging.info(json.dumps(data))
        make_response(json.dumps({"status": "ok"}), 200)

    return app
