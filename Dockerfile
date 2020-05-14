FROM python:3-slim-buster

RUN apt-get -q update
RUN apt-get -qqy install git

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

ARG PRODUCTION=0
ENV PRODUCTION ${PRODUCTION:-0}

ARG CONFIG_FILE
ENV CONFIG_FILE ${CONFIG_FILE}

ARG HOSTS_FILE
ENV HOSTS_FILE ${HOSTS_FILE}

ARG DATABASE_HOST
ENV DATABASE_HOST ${DATABASE_HOST}

ARG DATABASE_NAME
ENV DATABASE_NAME ${DATABASE_NAME}

ARG DATABASE_USER
ENV DATABASE_USER ${DATABASE_USER}

ARG DATABASE_PASSWORD
ENV DATABASE_PASSWORD ${DATABASE_PASSWORD}

ENV WORKERS 2

COPY . /code/

EXPOSE 8000

CMD gunicorn --worker-class=gevent --capture-output --access-logfile /var/log/gunicorn.log --error-logfile /var/log/gunicorn.err.log --workers ${WORKERS} --bind 0.0.0.0:8000 dockerizer.wsgi
