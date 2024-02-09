import codecs
from pathlib import Path

from appdirs import user_cache_dir
from rich import progress

from . import __name__ as name

_fcbgvsl = codecs.encode("fcbgvsl", "rot13")

ENVVAR_PREFIX = name.upper()
CACHE_HOME = Path(user_cache_dir(name, "drunkontee"))
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
