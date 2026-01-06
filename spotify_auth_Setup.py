import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Replace with your credentials from .env
SPOTIFY_CLIENT_ID, = "<your-spotify-client-id>"
SPOTIFY_CLIENT_SECRET, = "<your-spotify-client-secret>"
SPOTIFY_REDIRECT_URI, = "<your-spotify-redirect-uri>"

# Required scopes for the bot
SCOPES = "user-read-currently-playing user-read-playback-state user-top-read user-library-read playlist-read-private"

# Create auth manager
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
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