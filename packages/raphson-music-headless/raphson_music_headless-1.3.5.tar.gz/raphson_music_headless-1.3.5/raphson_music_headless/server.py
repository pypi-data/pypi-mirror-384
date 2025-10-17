from asyncio import Task
import asyncio
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any, cast

from aiohttp import web
from aiohttp.web_app import Application
from raphson_mp.client import RaphsonMusicClient
from raphson_mp.common.lyrics import ensure_plain
from raphson_mp.common.track import NEWS_PATH

from .config import Config
from .downloader import Downloader
from .player import AudioPlayer

_LOGGER = logging.getLogger(__name__)


class App:
    _tasks: set[Task[None]] = set()
    config: Config
    client: RaphsonMusicClient
    player: AudioPlayer
    downloader: Downloader
    last_news_queue: datetime = datetime.fromtimestamp(0)

    def __init__(self, config: Config):
        self.config = config
        self.client = RaphsonMusicClient()
        self.downloader = Downloader(self.client, config)

        if config.player == "mpv":
            from raphson_music_headless.player.mpv_player import MPVAudioPlayer

            self.player = MPVAudioPlayer(self.client, self.downloader, config)
        elif config.player == "vlc":
            from raphson_music_headless.player.vlc_player import VLCAudioPlayer

            self.player = VLCAudioPlayer(self.client, self.downloader, config)
        else:
            raise ValueError("invalid player: ", self.player)

    async def _queue_news_task(self):
        while True:
            await asyncio.sleep(60)

            now = datetime.now()
            if (
                self.config.news
                and self.player.is_playing()
                and now.minute > 11
                and now.minute < 15
                and now - self.last_news_queue > timedelta(minutes=10)
            ):
                self.last_news_queue = now
                try:
                    _LOGGER.info("queue news")
                    await self.downloader.enqueue(NEWS_PATH, True)
                except Exception:
                    _LOGGER.warning("Failed to enqueue news", exc_info=True)

    async def _root(self, _request: web.Request) -> web.StreamResponse:
        return web.FileResponse(Path(__file__).parent / "index.html")

    async def _state(self, _request: web.Request) -> web.StreamResponse:
        data: dict[str, Any] = {
            "name": self.config.name,
            "playlists": {
                "all": list(self.downloader.all_playlists.keys()),
                "enabled": self.downloader.enabled_playlists,
            },
            "player": {
                "has_media": self.player.has_media(),
                "is_playing": self.player.is_playing(),
                "position": self.player.position(),
                "duration": self.player.duration(),
                "volume": int(self.player.get_volume() * 100),
            },
        }
        if self.player.currently_playing and self.player.currently_playing.track:
            track = self.player.currently_playing.track
            data["currently_playing"] = track.to_dict()
        else:
            data["currently_playing"] = None

        return web.json_response(data)

    async def _image(self, _request: web.Request) -> web.StreamResponse:
        if self.player.currently_playing:
            return web.Response(
                body=self.player.currently_playing.image,
                status=200,
                content_type="image/webp",
            )

        return web.Response(status=404)

    async def _lyrics(self, _request: web.Request) -> web.StreamResponse:
        if self.player.currently_playing:
            lyrics = ensure_plain(self.player.currently_playing.track.parsed_lyrics)
            if lyrics:
                return web.Response(
                    body=lyrics.text,
                    status=200,
                    content_type="text/plain",
                )

        return web.Response(status=204)

    async def _list_tracks(self, request: web.Request) -> web.StreamResponse:
        playlist = request.query["playlist"]
        return web.Response(
            body=await self.client.list_tracks_response(playlist),
            status=200,
            content_type="application/json",
        )

    async def _stop(self, _request: web.Request) -> web.StreamResponse:
        await self.player.stop()
        return web.Response(status=204)

    async def _pause(self, _request: web.Request) -> web.StreamResponse:
        await self.player.pause()
        return web.Response(status=204)

    async def _play(self, _request: web.Request) -> web.StreamResponse:
        await self.player.play()
        return web.Response(status=204)

    async def _next(self, _request: web.Request) -> web.StreamResponse:
        await self.player.next(retry=False)
        return web.Response(status=204)

    async def _play_news(self, _request: web.Request) -> web.StreamResponse:
        await self.downloader.enqueue(NEWS_PATH, front=True)
        await self.player.next(retry=False)
        return web.Response(status=204)

    async def _seek(self, request: web.Request) -> web.StreamResponse:
        position = int(await request.text())
        await self.player.seek(position)
        return web.Response(status=204)

    async def _volume(self, request: web.Request) -> web.StreamResponse:
        volume = int(await request.text())
        self.player.set_volume(volume / 100)
        return web.Response(status=204)

    async def _playlists(self, request: web.Request) -> web.StreamResponse:
        playlists = cast(list[str], await request.json())
        assert isinstance(playlists, list)
        for playlist in playlists:
            assert isinstance(playlist, str)
            assert playlist in self.downloader.all_playlists
        _LOGGER.info("Changed enabled playlists: %s", playlists)
        self.downloader.enabled_playlists = playlists
        return web.Response(status=204)

    async def _enqueue(self, request: web.Request) -> web.StreamResponse:
        await self.downloader.enqueue(await request.text())
        return web.Response(status=204)

    async def _play_track(self, request: web.Request) -> web.StreamResponse:
        await self.downloader.enqueue(await request.text(), front=True)
        await self.player.next(retry=False)
        return web.Response(status=204)

    async def setup(self, _app: Application):
        await self.client.setup(
            base_url=self.config.server,
            user_agent="Raphson-Music-Headless",
            token=self.config.token,
        )
        await self.downloader.setup()
        await self.player.setup()
        self._tasks.add(asyncio.create_task(self._queue_news_task()))

    async def cleanup(self, _app: Application) -> None:
        _LOGGER.info("Stopping")
        await self.player.stop()
        await self.client.close()

    def start(self, config: Config):
        routes = [
            web.get("/", self._root),
            web.get("/state", self._state),
            web.get("/image", self._image),
            web.get("/lyrics", self._lyrics),
            web.get("/list_tracks", self._list_tracks),
            web.post("/stop", self._stop),
            web.post("/pause", self._pause),
            web.post("/play", self._play),
            web.post("/next", self._next),
            web.post("/play_news", self._play_news),
            web.post("/seek", self._seek),
            web.post("/volume", self._volume),
            web.post("/playlists", self._playlists),
            web.post("/enqueue", self._enqueue),
            web.post("/play_track", self._play_track),
        ]

        app = web.Application()
        app.add_routes(routes)
        app.on_startup.append(self.setup)
        app.on_cleanup.append(self.cleanup)

        _LOGGER.info('starting web server on %s:%s', config.host, config.port)

        web.run_app(app, host=config.host, port=config.port, print=None)
