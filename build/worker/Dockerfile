FROM python:3.7-alpine

ENV STREAM=venkman
ENV CONSUMER=paperboy
ENV CONSUMERID=one

WORKDIR /app

COPY ./protonpack /app/protonpack

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

RUN pip install -e .

CMD protonpackworker startup -s $STREAM -c $CONSUMER -i $CONSUMERID
