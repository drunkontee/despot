from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, TypeVar

from librespot.audio import SuperAudioFormat

from .constants import DATETIME_FORMAT

if TYPE_CHECKING:
    from librespot.proto import Metadata_pb2 as Metadata

_safefilename = re.compile(r'[/\\?%*:|"<>]')

T = TypeVar("T", str, int)


def make_safe_filename(value: T) -> T:
    if isinstance(value, str):
        return _safefilename.sub("-", value)
    return value


def get_filename_ext(codec: SuperAudioFormat) -> str:
    match codec:
        case SuperAudioFormat.MP3:
            return "mp3"
        case SuperAudioFormat.VORBIS:
            return "ogg"
        case SuperAudioFormat.AAC:
            return "m4a"
    raise NotImplementedError


def format_artist(value: Metadata.Artist) -> str:
    if (artist_count := len(value)) == 1:
        return value[0].name
    if artist_count > 1:
        return ", ".join(a.name for a in value[:-1]) + f" & {value[-1].name}"
    raise ValueError


def format_date(value: Metadata.Date) -> str:
    return datetime(
        value.year,
        value.month or 1,
        value.day or 1,
        value.hour or 0,
        value.minute or 0,
        tzinfo=timezone.utc,
    ).strftime(DATETIME_FORMAT)
