# Despot

[![version](https://img.shields.io/pypi/v/despot)](https://pypi.org/project/despot/)
![python](https://img.shields.io/pypi/pyversions/despot)
[![downloads](https://static.pepy.tech/badge/despot)](https://pepy.tech/project/despot)
[![unlicense](https://img.shields.io/badge/license-Unlicense-7cd958)](https://codeberg.org/drunkontee/despot/src/branch/main/LICENSE)

[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/docs/)
[![pre-commit](https://img.shields.io/badge/-pre--commit-f8b424?logo=pre-commit&labelColor=grey)](https://github.com/pre-commit/pre-commit)

A fast and simple client to free your music from that green streaming service.

![despot demo](https://codeberg.org/drunkontee/despot/media/branch/main/.assets/demo.gif)

## Setup

Install via [pipx](https://pipx.pypa.io/stable/):

```bash
pipx install despot
```

Despot follows [semver](https://semver.org/spec/v2.0.0.html) versioning. It is also available as container image `codeberg.org/drunkontee/despot`. Images are tagged as `v1.2.3`, `v1.2`, and `v1`, as well as `latest` pointing to the most recent version, for example:

```bash
docker run --tty --rm codeberg.org/drunkontee/despot:v0
docker run --tty --rm codeberg.org/drunkontee/despot:v0.5
docker run --tty --rm codeberg.org/drunkontee/despot:v0.5.0
docker run --tty --rm codeberg.org/drunkontee/despot:latest
```

## Usage

Download songs like so:

```bash
despot https://open.….com/track/07ZCaJfuutIaoDxYrkdzQY
```

You can pass multiple URLs at once. Partial URLs (just the path) work, too:

```bash
despot /track/07ZCaJfuutIaoDxYrkdzQY
```

By default, despot will place files in `./downloads`. You can use `--destination` to change the destination directory.

Use `--help` to see all other available options:

![`despot --help`](.assets/despot-help.svg)

## Notes

* Despot does not transcode audio. Transcoding is terrible, so you'll have to do that yourself.
* Despot uses fixed pattern for naming files within the destination directory:
  * Singular Tracks: `{artist} - {title}.{ext}`
  * Entire shows/podcasts and singular episodes: `{show}/{publish_time} - {o.title}.{ext}`
  * Albums and entire arists: `{album_artist}/{album} ({album_year})/{disc:02d}-{track:02d} {title}.{ext}`
  * Playlists: `{playlist_name}/{idx:03d} {artist_or_show} - {name}.{ext}`

    These are the only patterns. Deal with it.

## Disclaimer

Using this code to connect to the API of that green streaming service is probably forbidden by them, and downloading unencrypted files violates their TOS. You should not use this code. Pretty please with sugar on top.
