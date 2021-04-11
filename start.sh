#!/bin/bash

if [ $MUSICBOT_ENV == "prod" ]; then
  echo "> Prod environment, running with healthcheck API"
  ./musicbot.py &
  MUSICBOT_PID=$!

  echo "> Musicbot started (pid: ${MUSICBOT_PID})!"
  ./health_server.py $MUSICBOT_PID
else
  echo "> Dev environment, running standalone"
  ./musicbot.py
fi
