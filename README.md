# Spotify to YouTube Music Playlist Transfer

Transfer playlists from Spotify to YouTube Music.
Brutally vibe coded because I needed it, and you might too.

## Features

- Transfer public Spotify playlists to YouTube Music
- Track matching using song title, artist, and duration
- Logging of transfer process and missing tracks
- Configure via `.env` file or command line arguments
- Built with Python 3.11+ and Poetry

## Prerequisites

- Python 3.11+
- Poetry (dependency management)
- Spotify Developer Account (API access)
- YouTube Music subscription (recommended)

## Quick Start

1. Install dependencies:
   ```bash
   poetry install --no-root
   ```

2. Run setup:
   ```bash
   poetry run python setup_music_transfer.py
   ```

3. Transfer playlist:
   ```bash
   poetry run python spotify_to_youtube_music.py "PLAYLIST_URL" "New Playlist Name"
   ```

## Setup

### Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app and copy Client ID and Client Secret

### YouTube Music Authentication

1. Open [YouTube Music](https://music.youtube.com) and log in
2. Open Developer Tools (F12)
3. Go to Network tab, refresh page
4. Find request to `music.youtube.com`, copy as cURL
5. Use in setup script

### Configuration

Copy `.env.example` to `.env` and add your credentials:
```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

## Usage

Basic transfer:
```bash
poetry run python spotify_to_youtube_music.py "SPOTIFY_PLAYLIST_URL" "Playlist Name"
```

With credentials:
```bash
poetry run python spotify_to_youtube_music.py \
  --spotify-client-id "your_id" \
  --spotify-client-secret "your_secret" \
  "PLAYLIST_URL" "Playlist Name"
```

## Troubleshooting

- **Spotify API issues**: Check Client ID/Secret in `.env`
- **YouTube Music auth**: Re-run setup if `ytmusic_auth.json` is invalid
- **Missing tracks**: Check logs in `spotify_to_ytmusic.log`
- **Auth expired**: Get fresh browser headers from YouTube Music

## Limitations

- Public Spotify playlists only
- 85-95% track matching success rate
- Some tracks unavailable on YouTube Music
- Rate limiting on large playlists (1000+ tracks)

## License

MIT License
