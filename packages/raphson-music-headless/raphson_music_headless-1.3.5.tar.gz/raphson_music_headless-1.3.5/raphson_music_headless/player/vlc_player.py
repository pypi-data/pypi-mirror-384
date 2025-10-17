import asyncio
import logging
from tempfile import NamedTemporaryFile
from typing import Any, cast

from raphson_mp.client.track import DownloadedTrack
import vlc
from raphson_mp.client import RaphsonMusicClient
from typing_extensions import override

from raphson_music_headless.config import Config
from raphson_music_headless.downloader import Downloader
from raphson_music_headless.player import AudioPlayer

_LOGGER = logging.getLogger(__name__)  # noqa: F821


class VLCAudioPlayer(AudioPlayer):
    start_timestamp: int = 0
    temp_file: Any = None
    vlc_instance: vlc.Instance
    vlc_player: vlc.MediaPlayer
    vlc_events: vlc.EventManager

    def __init__(
        self, client: RaphsonMusicClient, downloader: Downloader, config: Config
    ):
        super().__init__(client, downloader, config)

        self.vlc_instance = vlc.Instance(
            "--file-caching=0"
        )  # pyright: ignore[reportAttributeAccessIssue]
        if not self.vlc_instance:
            raise ValueError("Failed to create VLC instance")
        self.vlc_player = self.vlc_instance.media_player_new()
        self.vlc_events = self.vlc_player.event_manager()

    @override
    def _setup(self):
        loop = asyncio.get_running_loop()

        def on_media_end(_event: Any):
            asyncio.run_coroutine_threadsafe(self._on_media_end(), loop)

        self.vlc_events.event_attach(
            vlc.EventType.MediaPlayerEndReached,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType]
            on_media_end,
        )

    @override
    def _play(self):
        self.vlc_player.play()

    @override
    def _pause(self) -> None:
        self.vlc_player.set_pause(True)

    @override
    def _stop(self) -> None:
        try:
            self.vlc_player.stop()
            self.vlc_player.set_media(None)
        finally:
            if self.temp_file:
                self.temp_file.close()

    @override
    def _set_media(self, track: DownloadedTrack) -> None:
        temp_file = NamedTemporaryFile("wb", prefix="rmp-playback-server-")
        try:
            temp_file.write(track.audio)

            media = self.vlc_instance.media_new(  # pyright: ignore[reportUnknownVariableType]
                temp_file.name
            )
            self.vlc_player.set_media(media)
            self.vlc_player.play()
        finally:
            # Remove old temp file
            if self.temp_file:
                self.temp_file.close()
            # Store current temp file so it can be removed later
            self.temp_file = temp_file

    @override
    def has_media(self) -> bool:
        return self.vlc_player.get_media() is not None

    @override
    def is_playing(self) -> bool:
        return cast(int, self.vlc_player.is_playing()) == 1

    @override
    def position(self) -> int:
        return cast(int, self.vlc_player.get_time()) // 1000

    @override
    def duration(self) -> int:
        return cast(int, self.vlc_player.get_length()) // 1000

    @override
    def _seek(self, position: float):
        _LOGGER.info("Seek to:", position)
        self.vlc_player.set_time(int(position * 1000))
        asyncio.create_task(self._submit_now_playing())

    @override
    def get_volume(self) -> float:
        return cast(int, self.vlc_player.audio_get_volume() / 100)

    @override
    def set_volume(self, volume: float) -> None:
        self.vlc_player.audio_set_volume(int(volume * 100))
