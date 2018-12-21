#!/bin/sh

pip install --upgrade pip

pip install watchdog

pip install -r requirements-test.txt
pip install -e .

FLASK_ENV=development FLASK_APP=protonpack.service flask run --host=0.0.0.0
