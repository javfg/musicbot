# Changelog


## 3.0.4

*Released on June 13, 2026*

* Add `/help` command to show usage instructions (`351119f`)


## 3.0.3

*Released on June 13, 2026*
* Change `/ranking` command to show all-time ranking instead of monthly (`381d8d6`)


## 3.0.2

*Released on April 13, 2026*

* Faster migration, reuse db connection (`8fc0ef5`)
* Fix digests breaking because of missing chat_id (`1f2545a`)


## 3.0.1

*Released on April 13, 2026*

* Fix digest links (`d9c8e5b`)
* Amend filtering (`dd399ef`)


## 3.0.0

*Released on April 4, 2026*

* Updated to python 3.14
* Updated to python-telegram-bot 22.7
* Made async
* Switched to using `uv`, `ruff` and `ty`
* Use per-chat SQLite dbs instead of TinyDB
* Integrated search with inline queries
* Many more providers, not only Spotify and YouTube
* Scrobbles now show a lot more info and links
* You can now amend fields by replying to a scrobble


## 0.2.1

*Released on August 22, 2023*

* Updated youtube_dl to latest version (`54379e7`)
* Fix crash when youtube_dl errors don't have a `msg` field (`144e867`)
* Allow whitespace between `!` and the command / uri (`9f9a16d`)
* Switched to vscode black formatting extension (`9950d64`)

## 0.2.0

* Initial public release
