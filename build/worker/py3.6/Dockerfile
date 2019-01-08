FROM python:3.6-alpine

ENV STREAM=venkman
ENV CONSUMER=paperboy
ENV CONSUMERID=one

WORKDIR /app

COPY ./protonpack /app/protonpack

COPY ./requirements.txt /app/requirements.txt
COPY ./VERSION /app/VERSION
COPY ./MANIFEST.in /app/MANIFEST.in
COPY ./setup.py /app/setup.py

RUN pip install -r requirements.txt

RUN pip install -e .

CMD protonpackworker startup -s $STREAM -c $CONSUMER -i $CONSUMERID
