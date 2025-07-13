#!/usr/bin/env python3
"""Transfer Spotify playlists to YouTube Music"""

import argparse
import json
import logging
import os
import re
import sys
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    from ytmusicapi import YTMusic
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required packages. Install with: poetry install")
    sys.exit(1)


class SpotifyToYouTubeMusic:
    
    def __init__(self):
        load_dotenv()
        self.spotify = None
        self.ytmusic = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spotify_to_ytmusic.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def setup_spotify(self, client_id: str = None, client_secret: str = None) -> bool:
        try:
            client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                self.logger.error("Spotify credentials not found. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")
                return False
            
            client_credentials_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            
            self.spotify.user_playlists('spotify', limit=1)
            self.logger.info("Spotify API connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Spotify: {e}")
            return False
    
    def setup_youtube_music(self, auth_file: str = None) -> bool:
        try:
            auth_file = auth_file or os.getenv('YTMUSIC_AUTH_FILE') or 'ytmusic_auth.json'
            
            if not os.path.exists(auth_file):
                self.logger.info(f"YouTube Music auth file not found at {auth_file}")
                self.logger.info("Run 'ytmusicapi oauth' to setup authentication")
                return False
            
            self.ytmusic = YTMusic(auth_file)
            self.logger.info("YouTube Music API connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup YouTube Music: {e}")
            return False
    
    def extract_spotify_playlist_id(self, url: str) -> Optional[str]:
        try:
            if 'open.spotify.com' in url:
                match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
                if match:
                    return match.group(1)
            
            if url.startswith('spotify:playlist:'):
                return url.split(':')[-1]
            
            if re.match(r'^[a-zA-Z0-9]+$', url):
                return url
            
            self.logger.error(f"Could not extract playlist ID from: {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting playlist ID: {e}")
            return None
    
    def get_spotify_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        try:
            tracks = []
            results = self.spotify.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track = item['track']
                        track_info = {
                            'name': track['name'],
                            'artists': [artist['name'] for artist in track['artists']],
                            'album': track['album']['name'],
                            'duration_ms': track['duration_ms'],
                            'popularity': track['popularity'],
                            'spotify_id': track['id']
                        }
                        tracks.append(track_info)
                
                results = self.spotify.next(results) if results['next'] else None
            
            self.logger.info(f"Found {len(tracks)} tracks in Spotify playlist")
            return tracks
            
        except Exception as e:
            self.logger.error(f"Error fetching Spotify playlist: {e}")
            return []
    
    def search_youtube_music_track(self, track: Dict) -> Optional[str]:
        try:
            artists_str = ', '.join(track['artists'])
            query = f"{track['name']} {artists_str}"
            
            search_results = self.ytmusic.search(query, filter='songs', limit=5)
            
            if not search_results:
                self.logger.warning(f"No results found for: {query}")
                return None
            
            best_match = self._find_best_match(track, search_results)
            
            if best_match:
                self.logger.debug(f"Found match for '{track['name']}': {best_match['title']}")
                return best_match['videoId']
            else:
                self.logger.warning(f"No suitable match found for: {query}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error searching YouTube Music for '{track['name']}': {e}")
            return None
    
    def _find_best_match(self, spotify_track: Dict, yt_results: List[Dict]) -> Optional[Dict]:
        def similarity_score(yt_track: Dict) -> float:
            score = 0.0
            
            if self._normalize_string(spotify_track['name']) in self._normalize_string(yt_track['title']):
                score += 0.4
            
            spotify_artists = [self._normalize_string(a) for a in spotify_track['artists']]
            yt_artists = []
            
            if 'artists' in yt_track and yt_track['artists']:
                yt_artists = [self._normalize_string(a['name']) for a in yt_track['artists']]
            
            for sp_artist in spotify_artists:
                for yt_artist in yt_artists:
                    if sp_artist in yt_artist or yt_artist in sp_artist:
                        score += 0.3
                        break
            
            if 'duration_seconds' in yt_track and yt_track['duration_seconds']:
                spotify_duration = spotify_track['duration_ms'] / 1000
                yt_duration = int(yt_track['duration_seconds'])
                duration_diff = abs(spotify_duration - yt_duration)
                if duration_diff < 10:
                    score += 0.2
                elif duration_diff < 30:
                    score += 0.1
            
            return score
        
        best_track = None
        best_score = 0.0
        
        for yt_track in yt_results:
            score = similarity_score(yt_track)
            if score > best_score and score > 0.3:
                best_score = score
                best_track = yt_track
        
        return best_track
    
    def _normalize_string(self, s: str) -> str:
        return re.sub(r'[^\w\s]', '', s.lower()).strip()
    
    def create_youtube_playlist(self, name: str, description: str = "") -> Optional[str]:
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=name,
                description=description or f"Transferred from Spotify playlist"
            )
            self.logger.info(f"Created YouTube Music playlist: {name} (ID: {playlist_id})")
            return playlist_id
            
        except Exception as e:
            self.logger.error(f"Error creating YouTube playlist: {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        try:
            success_count = 0
            
            for track_id in track_ids:
                try:
                    self.ytmusic.add_playlist_items(playlist_id, [track_id])
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to add track {track_id}: {e}")
            
            self.logger.info(f"Successfully added {success_count}/{len(track_ids)} tracks to playlist")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error adding tracks to playlist: {e}")
            return False
    
    def transfer_playlist(self, spotify_url: str, youtube_playlist_name: str) -> bool:
        self.logger.info(f"Starting playlist transfer: {spotify_url} -> {youtube_playlist_name}")
        
        playlist_id = self.extract_spotify_playlist_id(spotify_url)
        if not playlist_id:
            return False
        
        spotify_tracks = self.get_spotify_playlist_tracks(playlist_id)
        if not spotify_tracks:
            self.logger.error("No tracks found in Spotify playlist")
            return False
        
        youtube_track_ids = []
        not_found = []
        
        for i, track in enumerate(spotify_tracks, 1):
            self.logger.info(f"Searching for track {i}/{len(spotify_tracks)}: {track['name']} by {', '.join(track['artists'])}")
            
            yt_track_id = self.search_youtube_music_track(track)
            if yt_track_id:
                youtube_track_ids.append(yt_track_id)
            else:
                not_found.append(f"{track['name']} by {', '.join(track['artists'])}")
        
        self.logger.info(f"Found {len(youtube_track_ids)} out of {len(spotify_tracks)} tracks on YouTube Music")
        
        if not_found:
            self.logger.warning(f"Could not find {len(not_found)} tracks:")
            for track in not_found:
                self.logger.warning(f"  - {track}")
        
        if not youtube_track_ids:
            self.logger.error("No tracks found on YouTube Music")
            return False
        
        yt_playlist_id = self.create_youtube_playlist(youtube_playlist_name)
        if not yt_playlist_id:
            return False
        
        success = self.add_tracks_to_playlist(yt_playlist_id, youtube_track_ids)
        
        if success:
            self.logger.info(f"Successfully transferred playlist! YouTube Music playlist ID: {yt_playlist_id}")
        
        return success


def main():
    parser = argparse.ArgumentParser(
        description='Transfer Spotify playlist to YouTube Music',
        epilog='Credentials can be provided via command line arguments or .env file. '
               'See .env.example for the required environment variables.'
    )
    parser.add_argument('spotify_url', help='Spotify playlist URL or ID')
    parser.add_argument('youtube_playlist_name', help='Name for the YouTube Music playlist')
    parser.add_argument('--spotify-client-id', help='Spotify Client ID (overrides SPOTIFY_CLIENT_ID from .env)')
    parser.add_argument('--spotify-client-secret', help='Spotify Client Secret (overrides SPOTIFY_CLIENT_SECRET from .env)')
    parser.add_argument('--ytmusic-auth', help='YouTube Music auth file path (overrides YTMUSIC_AUTH_FILE from .env, defaults to ytmusic_auth.json)')
    
    args = parser.parse_args()
    
    transfer_service = SpotifyToYouTubeMusic()
    
    if not transfer_service.setup_spotify(args.spotify_client_id, args.spotify_client_secret):
        print("Failed to setup Spotify API. Check your credentials in .env file or command line arguments.")
        sys.exit(1)
    
    if not transfer_service.setup_youtube_music(args.ytmusic_auth):
        print("Failed to setup YouTube Music API. Make sure ytmusic_auth.json exists.")
        sys.exit(1)
    
    success = transfer_service.transfer_playlist(args.spotify_url, args.youtube_playlist_name)
    
    if success:
        print("Playlist transfer completed successfully!")
    else:
        print("Playlist transfer failed. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()