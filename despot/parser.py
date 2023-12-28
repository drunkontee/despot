from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterator

from librespot.metadata import AlbumId, ArtistId, EpisodeId, PlaylistId, ShowId, TrackId
from librespot.util import Base62, bytes_to_hex
from rich.console import Console

from .constants import _fcbgvsl
from .enums import ItemType
from .logging import logger
from .models import DownloadableBatch, DownloadableTrack
from .utils import format_artist

if TYPE_CHECKING:
    from librespot.core import ApiClient, Session

_RE_ITEM_ID = r"/?(?P<item_id>[0-9a-zA-Z]{22})(?:\?si=.+?)?$"
_RE_ITEM_TYPE = rf"/?(?P<item_type>{'|'.join(ItemType)})"

ITEM_ID_RE = re.compile(_RE_ITEM_ID)
ITEM_PATH_RE = re.compile(_RE_ITEM_TYPE + _RE_ITEM_ID)
ITEM_URL_RE = re.compile(r"^(?:https?://)?open\.\w+\.com" + _RE_ITEM_TYPE + _RE_ITEM_ID)


_base62 = Base62.create_instance_with_inverted_character_set()


class LinkParser:
    _api: ApiClient
    _console: Console

    def __init__(self, session: Session, console: Console | None = None) -> None:
        self._api = session.api()
        self._console = console or Console(quiet=True)

    def parse(self, *, uri_or_link: str, originating_type: ItemType | None = None) -> Iterator[DownloadableBatch]:
        logger.debug("Parsing link {}", uri_or_link)
        if uri_or_link.startswith(_fcbgvsl + ":"):
            _, item_type, item_id_b62 = uri_or_link.split(":")
        elif (match := ITEM_URL_RE.match(uri_or_link)) or (match := ITEM_PATH_RE.match(uri_or_link)):
            item_type, item_id_b62 = match.groups()
        elif match := ITEM_ID_RE.match(uri_or_link):
            item_id_b62 = match.group("item_id")
            item_type = "track"
        else:
            logger.error("Invalid link: {}", uri_or_link)
            return []

        item_gid = self.get_hex_gid(item_id_b62)
        current_type = ItemType(item_type)
        logger.debug("Resolved link to {} with GID {}", current_type, item_gid)
        match current_type:
            # Podcasts
            case ItemType.EPISODE:
                yield DownloadableBatch(
                    type=current_type,
                    tracks=[self._parse_episode(item_gid, originating_type=originating_type or current_type)],
                    description=None,
                )
            case ItemType.SHOW:
                yield self._parse_show(item_gid)
            # Music
            case ItemType.TRACK:
                yield DownloadableBatch(
                    type=current_type,
                    tracks=[self._parse_track(item_gid, originating_type=originating_type or current_type)],
                    description=None,
                )
            case ItemType.ALBUM:
                yield self._parse_album(item_gid)
            case ItemType.ARTIST:
                yield from self._parse_artist(item_gid)
            case ItemType.PLAYLIST:
                yield self._parse_playlist(item_id_b62)
            case _:
                raise NotImplementedError

    @staticmethod
    def get_hex_gid(url_id: str) -> str:
        return bytes_to_hex(_base62.decode(url_id.encode(), 16))

    def _parse_track(self, gid: str, originating_type: ItemType = ItemType.TRACK) -> DownloadableTrack:
        logger.debug("Creating abstract track {} from originating type {}", gid, originating_type)
        return DownloadableTrack(track_id=TrackId(gid), originating_type=originating_type)

    def _parse_episode(self, gid: str, originating_type: ItemType = ItemType.EPISODE) -> DownloadableTrack:
        logger.debug("Creating abstract episode {} from originating type {}", gid, originating_type)
        return DownloadableTrack(track_id=EpisodeId(gid), originating_type=originating_type)

    def _parse_album(self, gid: str, originating_type: ItemType = ItemType.ALBUM) -> DownloadableBatch:
        with self._console.status("Fetching album metadata"):
            metadata = self._api.get_metadata_4_album(AlbumId(gid))

        artist = format_artist(metadata.artist)
        return DownloadableBatch(
            type=ItemType.ALBUM,
            tracks=[
                self._parse_track(gid=bytes_to_hex(track.gid), originating_type=originating_type)
                for disc in metadata.disc
                for track in disc.track
            ],
            description=f"album '{metadata.name}' by {artist}",
        )

    def _parse_show(self, gid: str, originating_type: ItemType = ItemType.SHOW) -> DownloadableBatch:
        with self._console.status("Fetching show metadata"):
            metadata = self._api.get_metadata_4_show(ShowId(gid))

        return DownloadableBatch(
            type=ItemType.SHOW,
            tracks=[
                self._parse_episode(bytes_to_hex(episode.gid), originating_type=originating_type)
                for episode in reversed(metadata.episode)
            ],
            description=f"episodes of {metadata.name}",
        )

    def _parse_artist(self, gid: str, originating_type: ItemType = ItemType.ARTIST) -> Iterator[DownloadableBatch]:
        with self._console.status("Fetching artist metadata"):
            metadata = self._api.get_metadata_4_artist(ArtistId(gid))

        for album_group in metadata.album_group:
            for album in album_group.album:
                yield self._parse_album(bytes_to_hex(album.gid), originating_type=originating_type)

    def _parse_playlist(self, gid: str, originating_type: ItemType = ItemType.PLAYLIST) -> DownloadableBatch:
        with self._console.status("Fetching playlist metadata"):
            metadata = self._api.get_playlist(PlaylistId(gid))

        tracks = DownloadableBatch(
            type=ItemType.PLAYLIST,
            description=f"playlist {metadata.attributes.name}",
            context={"playlist_name": metadata.attributes.name},
            tracks=[],
        )
        for track in metadata.contents.items:
            tracks += list(self.parse(uri_or_link=track.uri, originating_type=originating_type))
        return tracks
