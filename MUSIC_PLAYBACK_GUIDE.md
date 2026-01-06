# Music Playback Guide

This guide covers the new voice channel music playback features integrated with Spotify.

## Overview

The bot now supports playing music in Discord voice channels with full queue management, playback controls, and loop functionality. The music search is powered by Spotify's API, allowing you to search for and queue any track available on Spotify.

## Requirements

- **FFmpeg**: Required for audio playback in Discord voice channels
- **Spotify API credentials**: For music search functionality
- **Discord voice permissions**: Bot needs permission to connect to and speak in voice channels

## Installation

1. Install FFmpeg:
   - **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`

2. Ensure Spotify API credentials are configured in your `.env` file:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

## Music Commands

### Voice Connection

**`!join` or `!connect`**
- Joins your current voice channel
- Example: `!join`

**`!leave`, `!disconnect`, or `!dc`**
- Leaves the current voice channel and clears the queue
- Example: `!leave`

### Playback Controls

**`!play <query>` or `!p <query>`**
- Searches for a track on Spotify and adds it to the queue
- If the bot isn't in a voice channel, it will automatically join yours
- Example: `!play never gonna give you up`
- Example: `!p bohemian rhapsody queen`

**`!pause`**
- Pauses the current playback
- Example: `!pause`

**`!resume` or `!unpause`**
- Resumes paused playback
- Example: `!resume`

**`!skip`, `!next`, or `!s`**
- Skips the current track and plays the next one in queue
- Example: `!skip`

**`!stop`**
- Stops playback completely and clears the entire queue
- Example: `!stop`

### Queue Management

**`!queue` or `!q`**
- Displays the current queue with a rich embed showing:
  - Currently playing track
  - Up to 10 upcoming tracks
  - Loop status and volume level
- Example: `!queue`

**`!nowplaying`, `!np`, or `!current`**
- Shows detailed information about the currently playing track
- Example: `!np`

**`!clearqueue`, `!cq`, or `!clear`**
- Clears all tracks from the queue without stopping current playback
- Example: `!clearqueue`

**`!remove <position>` or `!rm <position>`**
- Removes a specific track from the queue by its position number
- Example: `!remove 3` (removes the 3rd track in queue)

**`!shuffle`**
- Randomly shuffles all tracks in the current queue
- Example: `!shuffle`

### Playback Options

**`!loop <mode>` or `!repeat <mode>`**
- Sets the loop mode for playback
- Modes:
  - `off` / `none` / `disable`: Disables looping
  - `track` / `song` / `one`: Loops the current track
  - `queue` / `all`: Loops the entire queue
- Example: `!loop track`
- Example: `!repeat queue`

**`!volume <0-100>`, `!vol <0-100>`, or `!v <0-100>`**
- Sets the playback volume (0-100)
- Example: `!volume 50`
- Example: `!vol 75`

## Usage Examples

### Basic Usage

1. Join a voice channel
2. Use `!play <song name>` to start playing music
3. The bot will automatically join your channel and start playback
4. Add more songs with `!play <song name>` to build a queue
5. Use `!skip` to skip tracks or `!pause`/`!resume` to control playback

### Queue Management Example

```
!play never gonna give you up
!play africa toto
!play don't stop believin
!queue                    # View the queue
!remove 2                 # Remove the 2nd song
!shuffle                  # Shuffle remaining songs
!loop queue              # Loop the entire queue
```

### Volume and Playback Control

```
!volume 60               # Set volume to 60%
!loop track             # Loop current track
!nowplaying             # See current track details
!pause                  # Pause playback
!resume                 # Resume playback
```

## Features

- **Queue System**: Add multiple tracks to a queue
- **Auto-join**: Bot automatically joins your voice channel when you use `!play`
- **Loop Modes**: Loop individual tracks or the entire queue
- **Volume Control**: Adjust playback volume from 0-100
- **Rich Embeds**: Beautiful display of queue and now playing information
- **Track Information**: See artist, album, duration, and who requested each track
- **Shuffle**: Randomize your queue order
- **Queue Management**: Remove specific tracks, clear queue, view upcoming songs

## Important Notes

1. **Audio Source**: The current implementation uses Spotify for searching tracks. For full playback, you'll need to integrate with a service like yt-dlp to download/stream audio from YouTube, as Spotify only provides 30-second preview URLs through their API.

2. **Production Implementation**: To enable actual audio playback, you'll need to:
   - Install yt-dlp: `pip install yt-dlp`
   - Implement audio source fetching in the `_play_next()` method
   - Use `discord.FFmpegPCMAudio` or `discord.PCMVolumeTransformer` for playback

3. **Permissions**: Ensure the bot has the following permissions:
   - Connect to voice channels
   - Speak in voice channels
   - View channels

4. **FFmpeg**: Must be installed and accessible in your system PATH for audio playback to work.

## Troubleshooting

**Bot doesn't join voice channel:**
- Ensure you're in a voice channel (not a stage channel)
- Check bot has permission to connect and speak
- Verify bot can see the voice channel

**No audio playback:**
- Verify FFmpeg is installed and in PATH
- Check bot has speak permissions
- Ensure audio source implementation is complete (see Production Implementation note)

**Queue not working:**
- Ensure bot is connected to a voice channel
- Try using `!queue` to see current state
- Use `!stop` and try again

**Volume commands not working:**
- Volume only affects audio playback when using PCMVolumeTransformer
- Ensure audio source is properly configured with volume support

## Support

For additional help or to report issues, refer to the main README.md or use the `/reportbug` slash command in Discord.
