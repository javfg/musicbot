# musicbot dockerfile!
# 2021-04-10

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


FROM base as run

WORKDIR /musicbot
RUN pip install --editable src/

CMD ["src/start.py"]
