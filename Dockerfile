FROM python:3-slim-buster

RUN apt-get -q update && apt-get -qqy install \
    git apt-transport-https ca-certificates curl gnupg-agent software-properties-common

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
RUN apt-get -q update && apt-get -qqy install docker-ce-cli && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG PRODUCTION=0
ENV PRODUCTION ${PRODUCTION:-0}

ARG CONFIG_DIR
ENV CONFIG_DIR ${CONFIG_DIR}

COPY . .

RUN groupadd -g 1001 notroot && useradd -u 1001 -g notroot notroot

USER notroot

CMD python run.py
