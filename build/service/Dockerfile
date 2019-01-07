FROM python:3.7-alpine

ENV FLASK_ENV=development

WORKDIR /app

COPY ./protonpack /app/protonpack

COPY ./requirements.txt /app/requirements.txt

RUN pip install requirements.txt

RUN pip install -e .

CMD FLASK_APP=protonpack.service flask run --host=0.0.0.0
