#!/bin/sh

pip install --upgrade pip

pip install watchdog

pip install -r requirements-test.txt
pip install -e .

SPY_LOG_LOGGER=json-clean SPY_LOG_LEVEL=DEBUG SPY_SHOW_META=False FLASK_ENV=development FLASK_APP=protonpack.service flask run --host=0.0.0.0
