from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from librespot.audio import PlayableContentFeeder
from librespot.audio.decoders import AudioQuality
from librespot.metadata import EpisodeId, TrackId

from .enums import ItemType
from .metadata import WrappedMetadata
from .utils import get_filename_ext


def _custom__str__(qual: AudioQuality) -> str:
    return qual.name.lower()


def _custom_missing_(value: str | int) -> AudioQuality:
    if isinstance(value, str):
        value = value.upper()
        for member in AudioQuality:
            if member.name == value:
                return member

    return AudioQuality._missing_(value)


AudioQuality.__str__ = _custom__str__
AudioQuality._missing_ = _custom_missing_


@dataclass
class DownloadableTrack:
    track_id: TrackId | EpisodeId
    originating_type: ItemType

    metadata: WrappedMetadata = field(init=False, repr=False)
    target_filename: Path = field(init=False, repr=False)

    def populate_metadata(
        self, *, stream: PlayableContentFeeder.LoadedStream, destination: Path, **filename_attrs: str | int
    ) -> None:
        self.metadata = WrappedMetadata(stream.track or stream.episode)
        self.target_filename = self.metadata.generate_filename(
            destination,
            originating_type=self.originating_type,
            ext=get_filename_ext(stream.input_stream.codec()),
            **filename_attrs,
        )

    @property
    def is_abstract(self) -> bool:
        return getattr(self, "metadata", None) is None

    @property
    def task_description(self) -> str:
        if isinstance(self.track_id, EpisodeId):
            return f"[blue]{self.metadata.get('publish_time')}[/] {self.metadata.get('name')}"
        return self.metadata.get("name")

    @property
    def header_description(self) -> str:
        if isinstance(self.track_id, EpisodeId):
            return f"episode '{self.metadata.get('name')}' of {self.metadata.get('show')}"
        return f"song '{self.metadata.get('name')}' by {self.metadata.get('artist')}"

    @cached_property
    def temp_filename(self) -> Path:
        target = self.target_filename
        return target.with_stem("." + target.stem).with_suffix(".part")


@dataclass
class DownloadableBatch:
    type: ItemType  # noqa: A003
    tracks: list[DownloadableTrack]
    description: str | None
    context: dict = field(default_factory=dict)

    def __add__(self, other: DownloadableBatch | list[DownloadableBatch]) -> DownloadableBatch:
        if isinstance(other, DownloadableBatch):
            self.tracks += other.tracks
        elif isinstance(other, list):
            for nested in other:
                self.tracks += nested.tracks
        else:
            raise NotImplementedError
        return self


@dataclass
class ProcessingResult:
    track: DownloadableTrack
    exception: BaseException | None = None
    interrupted: bool = False
