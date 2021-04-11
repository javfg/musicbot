# musicbot dockerfile!
# 2021-04-10

###########################################################
# Base container
FROM python:3.9.4 AS base
LABEL maintainer="Javier Ferrer <javier.f.g@um.es>"

WORKDIR /musicbot
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV MUSICBOT_ENV=${MUSICBOT_ENV} \
  PYTHONUNBUFFERED=1

###########################################################
# VS Code remote Container
FROM base AS dev

COPY requirements-dev.txt requirements-dev.txt
RUN pip install -r requirements-dev.txt

COPY . .
RUN pip install --editable .

CMD ["./start.sh"]

###########################################################
# Prod container
FROM base AS prod

COPY . .
RUN pip install .

CMD ["./start.sh"]
