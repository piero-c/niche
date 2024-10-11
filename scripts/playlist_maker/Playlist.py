# Module for the final playlist
from scripts.spotify_genre.SpotifyUser import SpotifyUser
from typing import TypedDict

class NicheTrack(TypedDict):
    artist     : str
    track      : str
    playcount  : int
    listeners  : int
    likeness   : int
    spotify_uri: str
    spotify_url: str
    lastfm_url : str

class PlaylistInfo(TypedDict):
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
        """
        Initializes the Playlist by creating it on Spotify and adding the provided tracks.

        Args:
            tracks (list[NicheTrack]): A list of tracks to add to the playlist.
            spotify_user (SpotifyUser): The authenticated Spotify user.
        """
        # Extract Spotify URIs from the provided tracks
        track_uris = [track['spotify_uri'] for track in tracks]
        track_uris = [uri for uri in track_uris if uri]

        # Create a new playlist with placeholder name and description
        playlist = spotify_user.user.user_playlist_create(
            user          = spotify_user.id,
            name          = playlist_info['name'],
            public        = True,
            description   = playlist_info['description'],
            collaborative = False
        )

        # Add the extracted tracks to the newly created playlist
        if(track_uris):
            # Spotify API allows adding up to 100 tracks per request
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                spotify_user.user.playlist_add_items(playlist_id=playlist['id'], items=batch)

        # Store playlist information as attributes
        self.id          = playlist['id']
        self.url         = playlist['external_urls']['spotify']
        self.name        = playlist['name']
        self.description = playlist['description']

    def __repr__(self):
        return f"Playlist(name='{self.name}', url='{self.url}')"