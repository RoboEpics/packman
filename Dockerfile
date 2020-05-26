FROM python:3-slim-buster

RUN apt-get -q update && apt-get -qqy install \
    git apt-transport-https ca-certificates curl gnupg-agent software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
RUN apt-get -q update && apt-get -qqy install docker-ce docker-ce-cli containerd.io && rm -rf /var/lib/apt/lists/*

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

COPY . /code/

CMD python run.py
