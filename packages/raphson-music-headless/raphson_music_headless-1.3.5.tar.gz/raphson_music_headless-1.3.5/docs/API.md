# API

## GET `/`

Basic web UI

## GET `/state`

```json
{
  "playlists": {
    "all": ["CB", "DK", "JK", "JM", "MA"], // List of all playlist names
    "enabled": ["CB", "JK"] // List of enabled playlist names
  },
  "player": {
    "has_media": true, // True when paused or playing, false when stopped.
    "is_playing": true, // True when playing, false when paused or stopped
    "position": 15, // Current playback position (-1 when stopped)
    "duration": 207, // Total track duration as reported by VLC (-1 when stopped)
    "volume": 100 // VLC volume (0-100, -1 when stopped, 0 at initial startup)
  },
  "currently_playing": { // May be null, if no media is present or if playing a virtual track like news
    "path": "JK/25. Resist and Bite.mp3",
    "duration": 207, // Duration as reported by the server. For seek bars, use the duration in the player section instead.
    "title": "Resist And Bite", // May be null
    "album": "War And Victory - Best Of...Sabaton", // May be null
    "album_artist": "Sabaton", // May be null
    "year": 2016, // May be null
    "artists": [ // May be empty, but never null
      "Sabaton"
    ]
  }
}
```

## GET `/image`

Album cover image for currently playing track. Responds with status code 400 if no track is playing.

## GET `/list_tracks?playlist=<playlist>`

List of tracks in a playlist. Directly returns the response from the music player endpoint: `/tracks/filter?playlist=<playlist>`

## POST `/stop`

Stop music, if currently playing. Nothing happens if no music is playing.

## POST `/pause`

Pauses music. Nothing happens if music is already paused or no music is playing.

## POST `/play`

If music is paused, playback is resumed. If no music was playing, a new track is loaded and started. If no playlists are enabled, nothing happens.

## POST `/next`

A new track is loaded from the next playlist, and started. If no playlists are enabled, nothing happens.

### POST `/play_news`

The latest available news is downloaded and played immediately, even if hourly news is disabled.

### POST `/seek`

Seek to position in seconds, provided as an integer in the request body.

### POST `/volume`

Set player volume. Post body should be set to an integer 0-100.

## POST `/playlists`

Set enabled playlists. Post body should be a json array of playlist names.

## POST `/enqueue`

Add track to queue. Post body should contain a track path.

## POST `/play_track`

Load a specific track and play it immediately. Post body should contain a track path.
