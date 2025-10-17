import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self, cast


@dataclass
class Config:
    host: str
    port: int
    server: str
    token: str
    name: str
    default_playlists: list[str]
    player: str
    cache_size: int
    news: bool
    history: bool
    now_playing: bool
    control: bool
    mpv_opts: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> Self:
        with open(path, "r") as config_file:
            config = cast(dict[str, Any], json.load(config_file))

        return cls(
            config.get("host", "127.0.0.1"),
            config.get("port", 8181),
            config["server"],
            config["token"],
            config.get("name", "Headless"),
            config.get("default_playlists", []),
            config["player"],
            config.get("cache_size", 4),
            config.get("news", False),
            config.get("history", True),
            config.get("now_playing", True),
            config.get("control", True),
            config.get("mpv_opts", {}),
        )
