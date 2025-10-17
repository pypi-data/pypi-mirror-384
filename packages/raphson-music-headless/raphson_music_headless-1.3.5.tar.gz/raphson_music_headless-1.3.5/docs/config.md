# Configuration file

* `host` (str, default "127.0.0.1"): Address to listen on
* `port` (int, default 8181): Port to listen on
* `server` (str, required): Server URL, like https://music.raphson.nl
* `token` (str, required): Authentication token, obtained from https://music.raphson.nl/token
* `default_playlists` (list[str], required): Playlists that are enabled by default
* `player` ("mpv" or "vlc", required): Player backend to use
* `cache_size` (int, default 4): Number of tracks to download for every playlist
* `news` (bool, default false): Play hourly news
* `history` (bool, default true): Record playback history
* `now_playing` (bool, default true): Show now playing status in activity
* `control` (bool, default true): Allow remote control

## Custom MPV options

Set custom mpv options, for example audio output device:

```json
{
    "mpv_opts": {
        "audio-device": "alsa/hdmi:CARD=sofhdadsp,DEV=0"
    }
}
```

Obtain the alsa device name from `aplay -L`.

The full list of options is available here: https://mpv.io/manual/master
