# Module for the final playlist
from auth.SpotifyUser import SpotifyUser
from typing import TypedDict

class NicheTrack(TypedDict):
    """Niche track obj

    Args:
        TypedDict
    """
    artist     : str
    track      : str
    spotify_uri: str
    spotify_url: str

class PlaylistInfo(TypedDict):
    """Playlist info obj

    Args:
        TypedDict
    """
    name       : str
    description: str

# Playlist Class
class Playlist:
    """Playlist Object

    Attributes:
        id (str): Spotify Playlist ID.
        url (str): Spotify Playlist URL.
        name (str): Name of the playlist.
        description (str): Description of the playlist.
    """
    def __init__(self, tracks: list[NicheTrack], playlist_info: PlaylistInfo, spotify_user: SpotifyUser) -> None:
        """Initialise the playlist

        Args:
            tracks (list[NicheTrack]): The tracks for the playlist
            playlist_info (PlaylistInfo): The metadata for the playlist
            spotify_user (SpotifyUser): Spotify Authenticated User to create the playlist for
        """
        # Extract Spotify URIs from the provided tracks
        track_uris = [track.get('spotify_uri') for track in tracks if 'spotify_uri' in track]

        # Create a new playlist with placeholder name and description
        playlist = spotify_user.client.user_playlist_create(
            user          = spotify_user.id,
            name          = playlist_info['name'],
            public        = True,
            description   = playlist_info['description'],
            collaborative = False
        )

        # Add the extracted tracks to the newly created playlist
        # Spotify API allows adding up to 100 tracks per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            spotify_user.client.playlist_add_items(playlist_id=playlist['id'], items=batch)

        # Store playlist information as attributes
        self.id          = playlist['id']
        self.url         = playlist['external_urls']['spotify']
        self.name        = playlist['name']
        self.description = playlist['description']

    def __repr__(self):
        return(f"Playlist(name='{self.name}', url='{self.url}')")