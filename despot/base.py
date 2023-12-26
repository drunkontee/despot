from __future__ import annotations

import itertools
from typing import Iterator

import rich_click as click
from librespot.core import Session
from rich import get_console
from rich.console import Console

from .batch import BatchProcessor
from .config import Config
from .constants import CACHE_HOME
from .logging import logger
from .models import ProcessingResult
from .parser import LinkParser


class Despot:
    config: Config
    console: Console = get_console()

    _link_parser: LinkParser
    _batch_processor: BatchProcessor

    def __init__(self, config: Config, ctx: click.RichContext | None = None) -> None:
        self.config = config

        if ctx:
            if ctx.console:
                self.console = ctx.console

            @ctx.call_on_close
            def _cleanup() -> None:
                if hasattr(self, "_batch_processor"):
                    self._batch_processor.shutdown()
        else:
            self.console = Console(quiet=True)

        session = self._get_session()
        self._link_parser = LinkParser(session=session, console=self.console)
        self._batch_processor = BatchProcessor(config=self.config, session=session, console=self.console)

    def _get_session(self) -> Session:
        with self.console.status("Authenticating"):
            CACHE_HOME.mkdir(parents=True, exist_ok=True)
            credentials_file = CACHE_HOME / "credentials.json"
            config = (
                Session.Configuration.Builder()
                .set_cache_dir(str(CACHE_HOME))
                .set_stored_credential_file(str(credentials_file))
                .build()
            )
            builder = Session.Builder(config)
            if credentials_file.exists():
                builder.stored_file(credentials_file)
            if (creds := builder.login_credentials) and creds.username == self.config.username:
                logger.debug("Found stored credentials, attempting login")
                try:
                    return builder.create()
                except Exception as exc:
                    logger.opt(exception=exc).info(
                        "Login failed with stored credentials, falling back to password auth."
                    )
            return builder.user_pass(self.config.username, self.config.password).create()

    def download(self, links: str | list[str]) -> tuple[int, list[ProcessingResult]]:
        if isinstance(links, str):
            links = [links]
        results = list(itertools.chain.from_iterable((self._parse_and_download(link) for link in links)))

        if (failures := self._batch_processor.failures) > 0:
            self.console.print(f"\n[red]Done with {failures} failure{'s' if failures>1 else ''}.\n")
        else:
            self.console.print("\n[bar.finished]Done.\n")
        return self._batch_processor.failures, results

    def _parse_and_download(self, link: str) -> Iterator[ProcessingResult]:
        for batch in self._link_parser.parse(uri_or_link=link):
            yield from self._batch_processor.process(batch)
