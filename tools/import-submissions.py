#!/usr/bin/env python3

import datetime  # noqa
import json
import os
import sys

from pathlib import Path

from musicbot.util.db import DBManager

if len(sys.argv) != 3:
    print("Usage: import-submissions db submission-json-file")
    exit(0)

db_name, submissions_filename = sys.argv[1:]

# first read the provided json file
try:
    with open(submissions_filename) as f:
        submissions = json.load(f)
except FileNotFoundError:
    print(f"File {submissions_filename} not found")

# then change into the musicbot root and init the db
path = Path("../musicbot")
os.chdir(path)

try:
    db = DBManager(db_name).get_db(db_name)
except Exception as e:
    print(f"Something went wrong: {e}")

# import the data
# TODO: Convert dates to datetime objects
db.submissions_db.insert_multiple(submissions)
