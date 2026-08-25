# Changelog

## 3.0.12
*Released on August 25, 2026*

* Follow redirects on Spotify shortened links like: https://open.spotify.com/s/...
  to resolve them to proper Spotify links when used as a search query (`2809a25`)
* Add a `--healthcheck` cli argument to avoid using curl and other stuff that may
  not be present in the docker image (`4df8e56`)


## 3.0.11
*Released on May 3, 2026*

* Improved the Spotify matching so it can find the correct artist/album/track out
  of a list of candidates, instead of choosing the first one (`f6eb1d8`)


## 3.0.10
*Released on May 2, 2026*

* Add support for scrobbling Musicbrainz links just like Spotify and YouTube
(`79b44e0`)


## 3.0.9
*Released on April 16, 2026*

* Add Genius as a lyrics provider, along with an amender for it (`51d4d7e`)


## 3.0.8
*Released on April 15, 2026*

* Add basic MusicBrainz amenders for artists, albums and tracks (`68db30e`)
* Message early if an user attempts to amend a scrobble that he didn't submit
  himself. Do this in a DM to the user so the chat doesn't get spammed (`c261e1e`)


## 3.0.7
*Released on April 14, 2026*

* Make the MusicBrainz album fill more lenient, falling back to a query without
  the year if the initial search fails (`8b4e3bb`)
* Add links like https://open.spotify.com/intl-es/album/2JOhTLLfVCTtfKta6Sy5MB
  (with the `/intl-??` part) to the Spotify regexes (`bbf169f`)
* Ensure search goes up to a release group in MusicBrainz, not just a release,
  so we don't end up without tags and broken links (`dea42f5`)


## 3.0.6
*Released on April 14, 2026*

* Improved Deezer fill accuracy, matching on a list of candidates (`eeee5c6`)
* Add basic Deezer amenders for artists, albums and tracks (`b18c098`)


## 3.0.5
*Released on April 13, 2026*

* Fix musicbrainz album link (`2b3ee4f`)


## 3.0.4
*Released on April 13, 2026*

* Add `/help` command to show usage instructions (`351119f`)


## 3.0.3
*Released on April 13, 2026*

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
*Released on February 20, 2022*

* Initial public release
