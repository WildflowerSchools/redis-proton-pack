#!/bin/sh

pip install --upgrade pip

pip install watchdog

pip install -r requirements.txt
pip install -e .

echo "SPY_LOG_LOGGER=json-clean SPY_LOG_LEVEL=DEBUG SPY_SHOW_META=False protonpackworker startup -s venkman -c paperboy -i one" > worker.sh

watchmedo auto-restart -d ./protonpack -R sh worker.sh
