#!/bin/sh

pip install --upgrade pip

pip install watchdog

pip install -r requirements.txt
pip install -e .

watchmedo auto-restart -d ./protonpack -R protonpackworker startup -s venkman -c paperboy -i one
