FROM python:3.9-slim

# Install deps and build deps
RUN set -eux \
        && apt-get -q update \
        && apt-get -qqy install libpq-dev gcc git apt-transport-https ca-certificates curl gnupg-agent software-properties-common \
        && curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
        && add-apt-repository \
              "deb [arch=amd64] https://download.docker.com/linux/debian \
               $(lsb_release -cs) \
               stable" \
        && apt-get -q update \
        && apt-get -qqy install docker-ce-cli \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
ENV USER worker
RUN addgroup --gid 1001 $USER && adduser -u 1001 --gid 1001 --shell /bin/sh --disabled-password --gecos "" $USER
WORKDIR /home/$USER
USER $USER

# Build
ENV PATH="/home/$USER/.local/bin:${PATH}"
COPY --chown=$USER:$USER requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY --chown=$USER:$USER . .

# Run
ENV PYTHONUNBUFFERED 1

ARG PRODUCTION=0
ENV PRODUCTION ${PRODUCTION:-0}

ARG CONFIG_DIR
ENV CONFIG_DIR ${CONFIG_DIR}

CMD python run.py
