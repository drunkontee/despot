from __future__ import annotations

from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from librespot.proto import Metadata_pb2 as Metadata
from mutagen.ogg import MutagenError
from mutagen.oggvorbis import OggVorbis

from despot.exceptions import FilenameTemplateError

from .enums import ItemType
from .logging import logger
from .utils import format_artist, format_date, make_safe_filename

MetadataType = TypeVar("MetadataType", Metadata.Track, Metadata.Episode)

_PROPERTY_MAP_TRACK: dict[str, Callable[[Metadata.Track], str | int]] = {
    "name": lambda x: x.name,
    "artist": lambda x: format_artist(x.artist),
    "artist_or_show": lambda x: format_artist(x.artist),
    "album": lambda x: x.album.name,
    "album_artist": lambda x: format_artist(x.album.artist),
    "album_year": lambda x: x.album.date.year,
    "disc": lambda x: x.disc_number,
    "track": lambda x: x.number,
}

_PROPERTY_MAP_EPISODE: dict[str, Callable[[Metadata.Episode], str | int]] = {
    "name": lambda x: x.name,
    "show": lambda x: x.show.name,
    "artist_or_show": lambda x: x.show.name,
    "publish_time": lambda x: format_date(x.publish_time),
}


class WrappedMetadata(Generic[MetadataType]):
    _metadata: MetadataType

    @cached_property
    def propmap(self) -> dict[str, Callable[[MetadataType], str | int]]:
        return _PROPERTY_MAP_TRACK if isinstance(self._metadata, Metadata.Track) else _PROPERTY_MAP_EPISODE

    def __init__(self, metadata: MetadataType) -> None:
        self._metadata = metadata

    def get(self, name: str, default: str | int = "") -> Any:
        value = default
        if getter := self.propmap.get(name):
            with suppress(AttributeError):
                value = getter(self._metadata)
        return value

    def _to_filename_parts(self) -> dict[str, str | int]:
        return {key: make_safe_filename(self.get(key)) for key in self.propmap}

    def generate_filename(
        self, destination: Path, originating_type: ItemType, ext: str, **filename_attrs: str | int
    ) -> Path:
        match originating_type:
            case ItemType.TRACK:
                tmpl = "{artist} - {name}.{ext}"
            case ItemType.SHOW | ItemType.EPISODE:
                tmpl = "{show}/{publish_time} - {name}.{ext}"
            case ItemType.ALBUM | ItemType.ARTIST:
                tmpl = "{album_artist}/{album} ({album_year})/{disc:02d}-{track:02d} {name}.{ext}"
            case ItemType.PLAYLIST:
                tmpl = "{playlist_name}/{idx:03d} {artist_or_show} - {name}.{ext}"
            case _:
                raise NotImplementedError
        try:
            return destination / tmpl.format(
                **self._to_filename_parts(),
                **filename_attrs,
                ext=ext,
            )
        except (ValueError, KeyError) as exc:
            raise FilenameTemplateError(f"Invalid field '{exc.args[0]}' for {originating_type} filename") from exc

    def _to_tags(self) -> dict[str, str | list[str]]:
        match self._metadata:
            case Metadata.Episode():
                return {
                    "TITLE": self.get("name"),
                    "ARTIST": [self.get("show")],
                    "ALBUMARTIST": [self.get("show")],
                    "ALBUM": [self.get("show")],
                    "DATE": self.get("publish_time"),
                }
            case Metadata.Track():
                return {
                    "TITLE": self.get("name"),
                    "ARTIST": [a.name for a in self._metadata.artist],
                    "ALBUMARTIST": [a.name for a in self._metadata.album.artist],
                    "ALBUM": self.get("album"),
                    "DATE": format_date(self._metadata.album.date),
                    "TRACK": str(self.get("track")),
                    "DISCNUMBER": str(self.get("disc")),
                }
        raise NotImplementedError

    def write_tags(self, filename: Path) -> None:
        obj = OggVorbis(filename)
        obj.update(self._to_tags())
        logger.debug("Writing tags to {}", filename)
        try:
            obj.save()
        except MutagenError:
            # OggPage.replace() raises an exception on first attempt for some
            # reason, but still manages to spit out a valid Ogg file. Just to be
            # sure, we repeat .save() here to make sure that it's actually
            # valid.
            obj.save()
