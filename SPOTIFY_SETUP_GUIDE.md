# Spotify Integration Setup Guide

This guide will walk you through setting up Spotify integration for your Wolfbot Discord bot.

## Overview

The Spotify integration allows your bot to:
- Display currently playing track on Spotify
- Search for tracks on Spotify
- Show your top tracks and artists
- List your playlists
- And more!

## Prerequisites

- Python 3.8 or higher
- A Spotify account (free or premium)
- Access to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Step 1: Install Required Package

First, install the spotipy library:

```bash
pip install spotipy
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 2: Create a Spotify Application

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create app"**
4. Fill in the application details:
   - **App name:** `Wolfbot` (or your bot name)
   - **App description:** `Discord bot with Spotify integration`
   - **Redirect URI:** `http://localhost:8888/callback`
   - **Which API/SDKs are you planning to use?** Check "Web API"
5. Agree to the terms and click **"Save"**
6. Click **"Settings"** to view your credentials

## Step 3: Get Your Client ID and Secret

1. In the Settings page, you'll see:
   - **Client ID** - Copy this
   - **Client Secret** - Click "View client secret" and copy it
2. Open your `.env` file (copy from `.env.template` if you haven't already)
3. Add your credentials:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

## Step 4: Get Authorization Token

To access your Spotify data, you need to authorize the application and get a refresh token.

### Method 1: Using Python Script (Recommended)

Create a file called `spotify_auth.py` in your project root:

```python
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Replace with your credentials from .env
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
REDIRECT_URI = "http://localhost:8888/callback"

# Required scopes for the bot
SCOPES = "user-read-currently-playing user-read-playback-state user-top-read user-library-read playlist-read-private"

# Create auth manager
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPES,
    open_browser=True
)

# Get the authorization URL
auth_url = sp_oauth.get_authorize_url()
print(f"\nPlease visit this URL to authorize the application:\n{auth_url}\n")

# Get the token
token_info = sp_oauth.get_access_token(as_dict=True)

if token_info:
    print("\n" + "="*50)
    print("SUCCESS! Copy this refresh token to your .env file:")
    print("="*50)
    print(f"\nSPOTIFY_REFRESH_TOKEN={token_info['refresh_token']}")
    print("\n" + "="*50)
else:
    print("Failed to get token. Please try again.")
```

Run the script:

```bash
python spotify_auth.py
```

This will:
1. Open your browser automatically
2. Ask you to log in to Spotify (if not already logged in)
3. Ask you to authorize the application
4. Display your refresh token

Copy the `SPOTIFY_REFRESH_TOKEN` value to your `.env` file.

### Method 2: Manual Authorization

If the automatic method doesn't work:

1. Go to this URL (replace `YOUR_CLIENT_ID` with your actual Client ID):
   ```
   https://accounts.spotify.com/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost:8888/callback&scope=user-read-currently-playing%20user-read-playback-state%20user-top-read%20user-library-read%20playlist-read-private
   ```

2. Log in and authorize the application
3. You'll be redirected to `http://localhost:8888/callback?code=XXXXX`
4. Copy the `code` value from the URL
5. Use a tool like Postman or curl to exchange the code for tokens:

```bash
curl -X POST "https://accounts.spotify.com/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_CODE_HERE" \
  -d "redirect_uri=http://localhost:8888/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

6. The response will contain a `refresh_token` - copy this to your `.env` file

## Step 5: Update Your .env File

Your `.env` file should now have all Spotify settings:

```env
SPOTIFY_CLIENT_ID=abc123def456
SPOTIFY_CLIENT_SECRET=xyz789uvw012
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_REFRESH_TOKEN=AQD...your_long_refresh_token_here...xyz
```

## Step 6: Test the Integration

Start your bot:

```bash
python src/bot.py
```

In Discord, try these commands:

- `!health` - Check if Spotify integration is working
- `!spotify` or `!sp` - Show what's currently playing
- `!spotifysearch <query>` - Search for tracks
- `!toptracks` - Show your top tracks
- `!topartists` - Show your top artists
- `!playlists` - Show your playlists

## Available Commands

### Spotify Information Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `!spotify` | `!sp`, `!nowlistening` | Show currently playing track with rich embed |
| `!spotifysearch <query>` | `!spsearch`, `!searchtrack` | Search for tracks on Spotify |
| `!toptracks [timeframe]` | `!mytoptracks` | Show your top tracks (short/medium/long) |
| `!topartists [timeframe]` | `!mytopartists` | Show your top artists (short/medium/long) |
| `!playlists` | `!myplaylists`, `!spotifyplaylists` | Show your Spotify playlists |

### Voice Playback Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `!join` | `!connect` | Join your current voice channel |
| `!leave` | `!disconnect`, `!dc` | Leave voice channel and clear queue |
| `!play <query>` | `!p` | Search and play a track (auto-joins voice) |
| `!pause` | - | Pause current playback |
| `!resume` | `!unpause` | Resume paused playback |
| `!skip` | `!next`, `!s` | Skip current track |
| `!stop` | - | Stop playback and clear queue |
| `!loop <mode>` | `!repeat` | Set loop mode (off/track/queue) |
| `!volume <0-100>` | `!vol`, `!v` | Set playback volume |
| `!queue` | `!q` | Display current queue with rich embed |
| `!nowplaying` | `!np`, `!current` | Show currently playing track in voice |
| `!clearqueue` | `!cq`, `!clear` | Clear the queue |
| `!remove <position>` | `!rm` | Remove track from queue by position |
| `!shuffle` | - | Shuffle the queue |

### Timeframe Options

For `!toptracks` and `!topartists`:
- `short` - Last 4 weeks
- `medium` - Last 6 months (default)
- `long` - All time

Example: `!toptracks short`

### Loop Modes

For `!loop` command:
- `off` / `none` / `disable` - Disable looping
- `track` / `song` / `one` - Loop current track
- `queue` / `all` - Loop entire queue

Example: `!loop track`

## Voice Playback Setup

For voice playback features to work, you need FFmpeg installed:

### Windows
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" under System Variables
   - Add the path to ffmpeg's `bin` folder
4. Restart your terminal/IDE

### Linux
```bash
sudo apt-get install ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

**Note:** Voice playback uses Spotify for track search. For full audio playback, the current implementation provides the framework. For production use with actual audio streaming, you'll need to integrate with yt-dlp or similar services to fetch audio streams, as Spotify API only provides 30-second preview URLs.

See [MUSIC_PLAYBACK_GUIDE.md](MUSIC_PLAYBACK_GUIDE.md) for detailed voice playback documentation.

## Troubleshooting

### "Spotify integration is not configured"

- Make sure all credentials in `.env` are correct
- Verify the refresh token is valid
- Check that `spotipy` is installed: `pip install spotipy`

### "Could not initialize Spotify client"

- Verify your Client ID and Secret are correct
- Check that the redirect URI in your `.env` matches the one in Spotify Dashboard
- Make sure the redirect URI in Spotify Dashboard is exactly: `http://localhost:8888/callback`

### "Token expired" or authentication errors

- Your refresh token may have expired
- Re-run the authorization script (`spotify_auth.py`) to get a new token
- Make sure you're using the `refresh_token`, not the `access_token`

### "Nothing is playing" when something is playing

- Make sure you're actually playing something on Spotify (not paused)
- The Spotify account must be the same one you authorized
- Try playing on Spotify Desktop app or web player (may not work with all devices)

### Module not found: spotipy

```bash
pip install spotipy
```

## Security Notes

⚠️ **IMPORTANT:**
- Never share your `.env` file or commit it to version control
- Keep your Client Secret and Refresh Token private
- Add `.env` to your `.gitignore` file
- The refresh token gives access to your Spotify account - treat it like a password

## API Rate Limits

Spotify API has rate limits:
- Be mindful of how often you query the API
- The bot includes basic error handling for rate limits
- If you hit rate limits, wait a few minutes before trying again

## Scopes Explained

The bot requests these scopes:
- `user-read-currently-playing` - See what you're currently playing
- `user-read-playback-state` - Get playback state information
- `user-top-read` - Access your top tracks and artists
- `user-library-read` - Access your saved tracks
- `playlist-read-private` - Access your private playlists

If you need additional features, you may need to add more scopes and re-authorize.

## Additional Resources

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotipy Documentation](https://spotipy.readthedocs.io/)
- [Spotify Authorization Guide](https://developer.spotify.com/documentation/general/guides/authorization-guide/)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all credentials in `.env` are correct
3. Check the bot console for error messages
4. Review the Spotify API documentation
5. Check the `README.md` for general bot setup

---

**Need help?** Open an issue on GitHub or check the bot's documentation.
