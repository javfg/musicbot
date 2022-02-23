#!/usr/bin/env python
# -*- coding: utf-8 -*-
# based on https://github.com/stevekrenzel/autoreload

import logging
import os
import subprocess
import time

from datetime import datetime
from glob import glob

from bottle import route, run
from sty import fg


logging.basicConfig(format="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def file_times():
    watched_files = glob("./[!venv]**/**/*.py", recursive=True)
    for file in watched_files:
        yield os.stat(file).st_mtime


def print_stdout(process):
    stdout = process.stdout
    if stdout is not None:
        print(stdout)


@route("/health")
def health():
    pid = os.getpid()
    res = {"pid": pid, "time": datetime.now().isoformat(), "status": "pass"}
    logger.debug(f"sending health check (pid: {pid})")

    return res


# if running in development mode, activate autoreload
env = os.environ["MUSICBOT_ENV"]

if env == "dev":
    print(fg.blue + "dev env, running with autoreload" + fg.rs)
    last_mtime = max(file_times())
    process = subprocess.Popen("musicbot")

    while True:
        print_stdout(process)
        max_mtime = max(file_times())

        if max_mtime > last_mtime:
            last_mtime = max_mtime
            print(fg.yellow + "restarting process" + fg.rs)
            process.kill()
            time.sleep(1)
            process = subprocess.Popen("musicbot")

        time.sleep(1)

else:
    print(fg.blue + "prod env, running with healthcheck" + fg.rs)
    subprocess.Popen("musicbot")
    run(port=5000, quiet=True)
