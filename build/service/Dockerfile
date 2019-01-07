FROM python:3.7-alpine

ENV FLASK_ENV=development

WORKDIR /app

COPY ./protonpack /app/protonpack

COPY ./requirements.txt /app/requirements.txt
COPY ./VERSION /app/VERSION
COPY ./MANIFEST.in /app/MANIFEST.in
COPY ./setup.py /app/setup.py

RUN pip install -r requirements.txt

RUN pip install -e /app

CMD FLASK_APP=protonpack.service flask run --host=0.0.0.0
