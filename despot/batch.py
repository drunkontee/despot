import pathlib
import shutil
from concurrent.futures import Future, ThreadPoolExecutor
from http import HTTPStatus
from io import BufferedWriter
from threading import Event, Lock
from time import sleep, time
from typing import Iterator

from click import Abort
from librespot.audio import ChannelManager, PlayableContentFeeder
from librespot.audio.decoders import VorbisOnlyAudioQuality
from librespot.core import ApiClient, Session
from librespot.metadata import EpisodeId, TrackId
from rich.console import Console
from rich.filesize import decimal as decimal_filesize
from rich.progress import Progress, TaskID

from .config import Config
from .constants import OGG_HEADER_SIZE, RICH_PROGRESS_COLUMNS
from .enums import ItemType
from .exceptions import ContentUnavailableError, StreamError
from .logging import logger
from .models import DownloadableBatch, DownloadableTrack, ProcessingResult


class BatchProcessor:
    config: Config

    successes: int = 0
    failures: int = 0

    _console: Console
    _executor: ThreadPoolExecutor
    _lock: Lock
    _stop: Event
    _tempfiles: list[pathlib.Path]
    _content_feeder: PlayableContentFeeder
    _quality_picker: VorbisOnlyAudioQuality
    _progress: Progress

    def __init__(self, config: Config, session: Session, console: Console | None = None) -> None:
        self.config = config

        self._executor = ThreadPoolExecutor(max_workers=1 if config.paranoia else config.concurrency)
        self._lock = Lock()
        self._stop = Event()
        self._console = console or Console(quiet=True)
        self._content_feeder = session.content_feeder()
        self._quality_picker = VorbisOnlyAudioQuality(config.quality)
        self._tempfiles = []

    def shutdown(self) -> None:
        self._stop.set()
        self._executor.shutdown(wait=False, cancel_futures=True)

        if hasattr(self, "_progress"):
            for task in self._progress.tasks or []:
                if not task.finished:
                    task.visible = False
            self._progress.stop()

        for tempfile in self._tempfiles:
            if tempfile.exists():
                logger.info("Removing unfinished temporary file '{}'", tempfile)
                tempfile.unlink()

        logger.debug("Completed batch processor shutdown")

    def process(self, batch: DownloadableBatch) -> Iterator[ProcessingResult]:
        self._tempfiles = []

        if self.config.newest_first and batch.type == ItemType.SHOW:
            logger.debug("Queueing latest episodes first")
            tracks = batch.tracks[::-1]
        else:
            tracks = batch.tracks

        with Progress(
            *RICH_PROGRESS_COLUMNS, console=self._console, disable=self.config.debug, transient=False
        ) as self._progress:
            self._progress.live.vertical_overflow = "visible"
            logger.debug("Queueing downloads for batch {}", batch)
            futures = []
            batch_size = len(tracks)
            for idx, track in enumerate(tracks):
                job = self._executor.submit(
                    self._download_track,
                    track=track,
                    batch_ctx=batch.context,
                    batch_idx=idx,
                    batch_size=batch_size,
                    batch_description=batch.description,
                )
                job.add_done_callback(self._callback)
                futures.append(job)
            for future in futures:
                yield future.result()

    def _download_track(
        self,
        *,
        track: DownloadableTrack,
        batch_ctx: dict,
        batch_idx: int,
        batch_size: int,
        batch_description: str | None = None,
    ) -> ProcessingResult:
        has_header = False
        result = ProcessingResult(track=track)
        if batch_idx == 0:
            self._console.print()
        task = self._progress.add_task("", total=None, batch_idx=batch_idx + 1, batch_size=batch_size)
        try:
            stream = self._load_stream(track_id=track.track_id)
            track.populate_metadata(stream=stream, destination=self.config.destination, idx=batch_idx + 1, **batch_ctx)
            if batch_idx == 0:
                self._console.print(
                    f"[bold bright_magenta]Downloading {batch_description or track.header_description}[/]\n"
                )
            has_header = True

            if self._bail_condition(task=task, track=track):
                return result

            total_size = stream.input_stream.size - OGG_HEADER_SIZE
            self._progress.update(task, description=track.task_description, total=total_size, visible=True)
            logger.debug("Downloading to {}", track.temp_filename)
            track.target_filename.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                self._tempfiles.append(track.temp_filename)
            with track.temp_filename.open("wb") as fp:
                if (download_duration := self._write_from_stream(fp, stream=stream, task=task)) == -1:
                    return result
                logger.debug(
                    "Done, {} took {:.2f} seconds to download ({}/s)",
                    track.temp_filename,
                    download_duration,
                    decimal_filesize(total_size / download_duration),
                )

            track.metadata.write_tags(track.temp_filename)
            logger.debug("Moving temp file to {}", track.target_filename)
            shutil.move(track.temp_filename, track.target_filename)

        except Exception as exc:
            result.exception = exc
            if track.originating_type in (ItemType.EPISODE, ItemType.TRACK) and not has_header:
                self._console.print(f"[bold red]<Unknown {track.originating_type} {track.track_id.hex_id()}>[/]\n")
            self._progress.update(task, description=f"[red]<{exc}>", visible=True)
            if self.config.debug:
                logger.opt(exception=exc).debug("Failure during download")
            if self.config.fail_early:
                raise Abort from exc

        return result

    def _write_from_stream(self, fp: BufferedWriter, stream: PlayableContentFeeder.LoadedStream, task: TaskID) -> float:
        start = next_chunk_start = time()
        while chunk := stream.input_stream.stream().read(ChannelManager.chunk_size):
            written = fp.write(chunk)
            self._progress.update(task, advance=written)
            chunk_duration = time() - next_chunk_start
            next_chunk_start = time()

            if self._stop.is_set():
                logger.debug("Stop event is set, bailing.")
                return -1

            if self.config.paranoia:
                sleep(max(1 - chunk_duration, 0))
        return time() - start

    def _bail_condition(self, *, task: TaskID, track: DownloadableTrack) -> bool:
        prefix = ""
        if track.target_filename.exists() and not self.config.overwrite:
            filesize = track.target_filename.stat().st_size
            prefix = "[bar.finished]Exists:[/] "
        elif self.config.dry_run:
            filesize = 0
            prefix = "[yellow]Dry-run:[/] "

        if prefix:
            self._progress.update(
                task,
                description=prefix + track.task_description,
                total=filesize,
                completed=filesize,
                visible=True,
            )
            return True
        return False

    def _load_stream(self, track_id: TrackId | EpisodeId, retries: int = 3) -> PlayableContentFeeder.LoadedStream:
        try:
            with self._lock:
                while retries > 0:
                    if stream := self._content_feeder.load(track_id, self._quality_picker, False, None):
                        return stream
                    retries -= 1
        except Exception as exc:
            if isinstance(exc, ApiClient.StatusCodeException) and exc.code == HTTPStatus.UNAVAILABLE_FOR_LEGAL_REASONS:
                raise ContentUnavailableError from exc
            raise StreamError from exc
        raise StreamError

    def _callback(self, result: Future[ProcessingResult] | ProcessingResult) -> None:
        if isinstance(result, Future):
            if result.cancelled():
                return
            if exc := result.exception():
                logger.error("Unexpected failure", exc_info=exc)
                return self._mark_failure()
            result = result.result()

        if not (exc := result.exception):
            return self._mark_success()

        return self._mark_failure()

    def _mark_success(self) -> None:
        with self._lock:
            self.successes += 1

    def _mark_failure(self) -> None:
        with self._lock:
            self.failures += 1
