# Changelog

## 1.3.5 2025-10-16
* Fix: playlist refresh task crashes when program is started without an internet connection

## 1.3.4 2025-10-06
* Fix: 'playing: true' when no media is loaded (player is stopped)
* Improve: web UI scale on mobile

## 1.3.3 2025-10-04
* Fix: stop doing nothing
* Fix: error in console when clicking Next in web UI

## 1.3.2 2025-10-03
* New: volume control in web UI
* Improve: faster updates of track information, lyrics and album cover in web UI
* Improve: improve web UI layout
* Fix: news queued multiple times
* Fix: next track not being played when current track finishes playing (broken in v1.3.1)

## 1.3.1 2025-09-24
* Fix: lyrics missing when connected to music server v2.9.0+

## 1.3.0 2025-07-24
* New: player sync / remote control support
* New: setting for custom MPV options
* Improve: immediately send new position to server on seek
* Improve: notify server on shutdown or player stop
* Fix: hang on corrupt track

## 1.2.5 2025-06-25
* New: option to configure client name
* New: options to disable remote control, now playing, history
* New: short options
* Fix: require mpv 1.0.8 containing an important bug fix to play_bytes

## 1.2.4 2025-06-13
* Improve: send volume to server
* Fix: missing remote control in newer raphson_mp server versions

## 1.2.3 2025-04-09
* Fix: dependency on older version of raphson_mp

## 1.2.2 2025-04-09
* Fix: no longer requires both VLC and MPV to be installed; only the one that is actually used
* Fix: music sometimes stopping when going to the next track

## 1.2.1 2024-12-26
* Improve: updated to work with newest raphson_mp version
* Fix: mpv play fixes

## 1.2.0 2024-12-14
* New: support control via websocket
* Fix: lyrics not shown in web UI
* Fix: update now playing for new music server version

## 1.1.0 2024-11-29
* New: mpv player support (selected by default)
* New: Debian package
* Improve: web page layout and theming
* Improve: don't print full news exception

## 1.0.1 2024-11-23

* Fix: handle errors when downloading news
* Fix: missing log arguments
* Fix: missing main function for raphson-music-headless script

## 1.0.0 2024-11-23

Initial release
