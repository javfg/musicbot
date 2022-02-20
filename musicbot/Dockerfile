# musicbot dockerfile!
# 2021-04-10

###########################################################
# Base container
FROM python:3.10.2-bullseye AS base
LABEL maintainer="Javier Ferrer <javier.f.g@um.es>"

WORKDIR /musicbot

ENV MUSICBOT_ENV=${MUSICBOT_ENV}
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY src/requirements.txt src/
RUN pip install --upgrade pip \
  && pip install -r src/requirements.txt

COPY . .


###########################################################
# Dev container
FROM base AS dev

WORKDIR /musicbot
RUN pip install --editable src/

CMD ["src/start.py"]


###########################################################
# Prod container
# TODO : MUST CHECK THIS
FROM base AS prod

WORKDIR /musicbot
RUN pip install src/

CMD ["src/start.py"]
