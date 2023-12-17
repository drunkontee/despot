# Despot

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

A simple client to download music from that green streaming service.

## Setup and usage

Install via [pipx](https://pipx.pypa.io/stable/):

```bash
pipx install https://codeberg.org/drunkontee/despot.git
```

Download songs like so:

```bash
despot https://open.….com/track/07ZCaJfuutIaoDxYrkdzQY
```

Partial URLs (just the path) work just fine, too.

```bash
despot /track/07ZCaJfuutIaoDxYrkdzQY
```

By default, despot will place files in `./downloads`. You can use `--destination` to change the destination directory.

Use `--help` to see all other available options.

## Notes

* Despot does not transcode audio. Transcoding is terrible, so you'll have to do that yourself.
* Despot uses fixed pattern for naming files within the destination directory:
  * Singular Tracks: `{artist} - {title}.{ext}`
  * Entire shows/podcasts and singular episodes: `{show}/{publish_time} - {o.title}.{ext}`
  * Albums and entire arists: `{album_artist}/{album} ({album_year})/{disc:02d}-{track:02d} {title}.{ext}`

    These are the only patterns. Deal with it.

## Disclaimer

Using this code to connect to the API of that green streaming service is probably forbidden by them, and downloading unencrypted files violates their TOS. You should not use this code. Pretty please with sugar on top.
