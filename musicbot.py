#!/usr/bin/env python
# -*- coding: utf-8 -*-
# based on https://github.com/stevekrenzel/autoreload

import os
import subprocess
import time
from glob import glob

from colorama import Fore, Style


def file_times():
    watched_files = glob("./[!venv]**/**/*.py", recursive=True)
    for file in watched_files:
        yield os.stat(file).st_mtime


def print_stdout(process):
    stdout = process.stdout
    if stdout is not None:
        print(stdout)


# if running in development mode, activate autoreload
env = os.environ["MUSICBOT_ENV"]

if env == "dev":
    print(f"{Fore.BLUE}🛈 running with autoreload{Style.RESET_ALL}", flush=True)

    last_mtime = max(file_times())
    process = subprocess.Popen("musicbot")

    while True:
        print_stdout(process)
        max_mtime = max(file_times())

        if max_mtime > last_mtime:
            last_mtime = max_mtime
            print(f"{Fore.RED}⚠️ restarting process...{Style.RESET_ALL}", flush=True)
            process.kill()
            time.sleep(3)
            process = subprocess.Popen("musicbot")

        time.sleep(1)

else:
    from musicbot.musicbot import main

    main()
