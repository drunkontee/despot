from dataclasses import dataclass
from pathlib import Path

from .models import AudioQuality


@dataclass
class Config:
    destination: Path = Path("./downloads")
    quality: AudioQuality = AudioQuality.VERY_HIGH.name
    debug: bool = False
    fail_early: bool = False
    ipdb: bool = True
    dry_run: bool = False
    concurrency: int = 4
    overwrite: bool = False
    newest_first: bool = False
    paranoia: bool = False

    username: str = ""
    password: str = ""


DEFAULT_CONFIG = Config()
