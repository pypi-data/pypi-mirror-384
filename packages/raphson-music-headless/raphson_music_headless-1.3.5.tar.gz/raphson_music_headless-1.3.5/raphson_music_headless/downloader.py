import asyncio
import logging
from collections import deque

from aiohttp import ClientError
from raphson_mp.client import RaphsonMusicClient
from raphson_mp.client.track import DownloadedTrack
from raphson_mp.client.playlist import Playlist

from .config import Config

_LOGGER = logging.getLogger(__name__)


class Downloader:
    client: RaphsonMusicClient
    config: Config
    cache: dict[str, deque[DownloadedTrack]] = {}
    queue: list[DownloadedTrack] = []
    all_playlists: dict[str, Playlist] = {}
    previous_playlist: str | None = None
    enabled_playlists: list[str]

    def __init__(self, client: RaphsonMusicClient, config: Config):
        self.client = client
        self.config = config
        self.enabled_playlists = list(config.default_playlists)

    async def setup(self):
        asyncio.create_task(self._fill_cache_task())
        asyncio.create_task(self._update_playlists_task())

    async def _update_playlists_task(self):
        while True:
            await asyncio.gather(self.update_playlists(), asyncio.sleep(300))

    async def update_playlists(self):
        try:
            self.all_playlists = {
                playlist.name: playlist for playlist in await self.client.playlists()
            }
        except Exception as ex:
            _LOGGER.warning("failed to update playlists: %s", ex)

    async def _fill_cache_task(self):
        while True:
            await asyncio.gather(self.fill_cache(), asyncio.sleep(1))

    async def fill_cache(self):
        """
        Ensure cache contains enough downloaded tracks
        """
        if len(self.enabled_playlists) == 0:
            return

        for playlist_name in self.enabled_playlists:
            if playlist_name in self.cache:
                if len(self.cache[playlist_name]) >= self.config.cache_size:
                    continue
            else:
                self.cache[playlist_name] = deque()

            try:
                track = await self.client.choose_track(playlist_name)
                _LOGGER.info("Downloading track: %s", track.path)
                downloaded = await track.download(self.client)
                self.cache[playlist_name].append(downloaded)
            except ClientError as ex:
                _LOGGER.warning(
                    "failed to download track for playlist %s: %s",
                    ex,
                    playlist_name,
                )
                await asyncio.sleep(5)

    def select_playlist(self) -> str | None:
        """
        Choose a playlist to play a track from.
        """
        if len(self.enabled_playlists) == 0:
            _LOGGER.warning("No playlists enabled!")
            return None

        if self.previous_playlist:
            try:
                cur_index = self.enabled_playlists.index(self.previous_playlist)
                self.previous_playlist = self.enabled_playlists[
                    (cur_index + 1) % len(self.enabled_playlists)
                ]
            except ValueError:  # not in list
                self.previous_playlist = self.enabled_playlists[0]
        else:
            self.previous_playlist = self.enabled_playlists[0]

        return self.previous_playlist

    async def enqueue(self, track_path: str, front: bool = False) -> None:
        track = await self.client.get_track(track_path)
        download = await track.download(self.client)
        if front:
            self.queue.insert(0, download)
        else:
            self.queue.append(download)

    def get_track(self) -> DownloadedTrack | None:
        """
        Get the next track to play
        """
        if self.queue:
            return self.queue.pop(0)

        playlist = self.select_playlist()
        if playlist is None:
            return None

        if playlist not in self.cache or len(self.cache[playlist]) == 0:
            return None

        return self.cache[playlist].popleft()
