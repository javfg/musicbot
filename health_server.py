#! /usr/bin/env python3
# -*- coding: utf-8 -*-import json

import json
import logging
import os
import sys
from datetime import datetime

from flask import Flask
from flask_api import status

if not len(sys.argv) == 2:
    print("Usage: health_check.py [pid]")
    exit

# Logging.
logging.basicConfig(format="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Start healthcheck server.
health_server = Flask(__name__)


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return "fail"
    else:
        return "pass"


@health_server.route("/health")
def health():
    pid = int(sys.argv[1])
    health_check = check_pid(pid)
    res = {
        "pid": pid,
        "time": datetime.now().isoformat(),
        "status": health_check,
    }
    code = status.HTTP_200_OK if health_check == "pass" else status.HTTP_503_SERVICE_UNAVAILABLE

    logger.debug(f"sending health check (pid: {pid}): {health_check}")

    return json.dumps(res), code


health_server.run()
