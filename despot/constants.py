import codecs
from os import environ
from pathlib import Path

from rich import progress

from . import __name__ as name

_fcbgvsl = codecs.encode("fcbgvsl", "rot13")

ENVVAR_PREFIX = name.upper()


def _resolve_cache_home() -> Path:
    if envvar := environ.get(f"{ENVVAR_PREFIX}_HOME"):
        path = Path(envvar)
    else:
        prefix = environ.get("XDG_CACHE_HOME") or "~/.cache"
        path = Path(prefix) / name
    return path.expanduser().resolve()


CACHE_HOME = _resolve_cache_home()
DATETIME_FORMAT = "%Y-%m-%d"

OGG_HEADER_SIZE = 0xA7

RICH_PROGRESS_COLUMNS = (
    progress.SpinnerColumn(finished_text="[bar.finished]✔️"),
    progress.TextColumn("[bar.complete]{task.fields[batch_idx]}/{task.fields[batch_size]}", justify="right"),
    progress.TextColumn("[progress.description]{task.description}"),
    progress.BarColumn(bar_width=25),
    progress.TaskProgressColumn(),
    progress.TimeRemainingColumn(),
    progress.DownloadColumn(),
    progress.TransferSpeedColumn(),
)
