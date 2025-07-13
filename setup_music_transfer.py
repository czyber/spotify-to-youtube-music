#!/usr/bin/env python3
"""Setup script for Spotify to YouTube Music playlist transfer"""

import os
import sys
import subprocess
import json
from typing import Dict, Any


def check_poetry_installation():
    try:
        result = subprocess.run(['poetry', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Poetry found: {result.stdout.strip()}")
        else:
            print("✗ Poetry not found. Please install Poetry first:")
            print("  curl -sSL https://install.python-poetry.org | python3 -")
            return False
    except FileNotFoundError:
        print("✗ Poetry not found. Please install Poetry first:")
        print("  curl -sSL https://install.python-poetry.org | python3 -")
        return False
    
    try:
        result = subprocess.run(['poetry', 'check'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Dependencies not installed. Installing now...")
            subprocess.check_call(['poetry', 'install', '--no-root'])
            print("✓ Dependencies installed successfully")
        else:
            print("✓ Dependencies are already installed")
    except subprocess.CalledProcessError:
        print("✗ Failed to install dependencies")
        return False
    
    return True


def setup_spotify_credentials():
    print("\n=== Spotify API Setup ===")
    print("1. Go to https://developer.spotify.com/dashboard")
    print("2. Log in with your Spotify account")
    print("3. Click 'Create an App'")
    print("4. Fill in app name and description")
    print("5. Copy your Client ID and Client Secret")
    print()
    
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("✗ Both Client ID and Client Secret are required")
        return False
    
    env_content = f"""SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ Spotify credentials saved to .env file")
    
    return True


def setup_youtube_music():
    print("\n=== YouTube Music Authentication Setup ===")
    print("YouTube Music uses browser-based authentication.")
    print("You'll need to get request headers from your browser.")
    print()
    print("Steps:")
    print("1. Open https://music.youtube.com in your browser")
    print("2. Log in to your YouTube Music account")
    print("3. Open Developer Tools (F12 or Cmd+Option+I)")
    print("4. Go to the Network tab")
    print("5. Refresh the page")
    print("6. Find a request to music.youtube.com")
    print("7. Right-click → Copy → Copy as cURL")
    print()
    
    print("When you have the cURL command, you can:")
    print("• Run the main script - it will guide you through authentication")
    print("• Or manually set up authentication using ytmusicapi browser")
    print()
    
    choice = input("Do you want to continue without setting up YouTube Music now? (y/n): ").lower()
    
    if choice == 'y':
        print("✓ Skipping YouTube Music setup for now")
        return True
    else:
        print("Please set up YouTube Music authentication manually:")
        print("  poetry run ytmusicapi browser --file ytmusic_auth.json")
        return False


def show_usage_examples():
    print("\n=== Usage Examples ===")
    print("After setup, you can transfer playlists using:")
    print()
    print("Basic usage:")
    print('  poetry run python spotify_to_youtube_music.py \\')
    print('    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" \\')
    print('    "My Awesome Playlist"')
    print()
    print("Using playlist ID only:")
    print('  poetry run python spotify_to_youtube_music.py \\')
    print('    "37i9dQZF1DXcBWIGoYBM5M" \\')
    print('    "My Awesome Playlist"')
    print()
    print("With custom YouTube Music auth file:")
    print('  poetry run python spotify_to_youtube_music.py \\')
    print('    --ytmusic-auth custom_auth.json \\')
    print('    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" \\')
    print('    "My Awesome Playlist"')
    print()
    print("For help:")
    print('  poetry run python spotify_to_youtube_music.py --help')


def main():
    print("Spotify to YouTube Music Transfer Setup")
    print("=" * 50)
    print("This setup will guide you through configuring the required")
    print("API credentials for both Spotify and YouTube Music.")
    print("=" * 50)
    
    if not check_poetry_installation():
        print("\n✗ Setup failed - Poetry is required")
        sys.exit(1)
    
    if not setup_spotify_credentials():
        print("\n✗ Setup failed during Spotify configuration")
        sys.exit(1)
    
    if not setup_youtube_music():
        print("\n✗ Setup failed during YouTube Music configuration")
        sys.exit(1)
    
    show_usage_examples()
    
    print("\n" + "=" * 50)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. If you skipped YouTube Music setup, run:")
    print("   poetry run ytmusicapi browser --file ytmusic_auth.json")
    print("2. Transfer a playlist:")
    print('   poetry run python spotify_to_youtube_music.py "PLAYLIST_URL" "NAME"')
    print("3. Check README.md for detailed instructions")
    print("=" * 50)


if __name__ == "__main__":
    main()