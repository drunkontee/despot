import pathlib
from typing import Any

import rich_click as click
from librespot.audio.decoders import AudioQuality

from . import __name__ as name
from .base import Despot
from .config import DEFAULT_CONFIG, Config
from .constants import ENVVAR_PREFIX, _fcbgvsl
from .enums import ItemType
from .logging import configure_logging

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.OPTIONS_PANEL_TITLE = "Miscellaneous Options"
click.rich_click.OPTION_GROUPS = {
    name: [
        {
            "name": "Basic parameters",
            "options": [
                "--username",
                "--password",
                "--destination",
                "--quality",
            ],
        },
        {
            "name": "Music-specific options",
            "options": [],
        },
        {
            "name": "Podcasts-specific options",
            "options": [
                "--newest-first",
            ],
        },
        {
            "name": "Processing parameters",
            "options": [
                "--paranoia",
                "--overwrite",
                "--concurrency",
            ],
        },
    ]
}


@click.command(
    context_settings={
        "auto_envvar_prefix": ENVVAR_PREFIX,
        "help_option_names": ["-h", "--help"],
    },
    help=f"Download music from {_fcbgvsl.title()} using the sharing link of any {ItemType.human_names()}.",
)
@click.argument(
    "links",
    nargs=-1,
    required=True,
)
@click.option(
    "-u",
    "--username",
    required=True,
    type=str,
    show_envvar=True,
    help="Your username on that green streaming service",
)
@click.option(
    "-p",
    "--password",
    required=True,
    prompt=True,
    hide_input=True,
    type=str,
    show_envvar=True,
    help="Your password on that green streaming service",
)
@click.option(
    "-d",
    "--destination",
    type=click.Path(
        exists=False,
        writable=True,
        file_okay=False,
        dir_okay=True,
        path_type=pathlib.Path,
    ),
    show_default=True,
    required=False,
    default=DEFAULT_CONFIG.destination,
    help="Directory to which to download the files",
)
@click.option(
    "-q",
    "--quality",
    type=click.Choice([str(q) for q in AudioQuality], case_sensitive=False),
    default=DEFAULT_CONFIG.quality,
    show_default=True,
    callback=lambda ctx, param, value: AudioQuality(value),
    help="Audio quality to download",
)
@click.option(
    "-P",
    "--paranoia",
    type=bool,
    default=DEFAULT_CONFIG.paranoia,
    is_flag=True,
    help="Paranoia mode, download files one by one at ~128KB/s (implies --concurrency=1)",
)
@click.option(
    "-o",
    "--overwrite",
    type=bool,
    default=DEFAULT_CONFIG.overwrite,
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "-nf",
    "--newest-first",
    type=bool,
    default=DEFAULT_CONFIG.newest_first,
    is_flag=True,
    help="Download episodes in descending order of publishing instead of ascending",
)
@click.option(
    "-c",
    "--concurrency",
    type=int,
    default=DEFAULT_CONFIG.concurrency,
    show_default=True,
    help="Maximum number of simultaneous downloads",
)
@click.option(
    "-n",
    "--dry-run",
    type=bool,
    default=DEFAULT_CONFIG.dry_run,
    is_flag=True,
    help="Don't actually download files",
)
@click.option(
    "-D",
    "--debug",
    type=bool,
    default=DEFAULT_CONFIG.debug,
    is_flag=True,
    help="Emit detailed diagnostic logging",
)
@click.option(
    "-F",
    "--fail-early",
    type=bool,
    default=DEFAULT_CONFIG.fail_early,
    is_flag=True,
    help="Abort at the first error. Useful together with --debug.",
)
@click.version_option(
    None,
    "-V",
    "--version",
    prog_name=__name__,
)
@click.pass_context
def main(ctx: click.RichContext, links: list[str], **kwargs: Any) -> int:
    config = Config(**kwargs)
    configure_logging(config.debug)
    d = Despot(config, ctx=ctx)
    return d.download(links)[0]
