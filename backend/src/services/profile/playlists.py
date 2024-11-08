from src.db.DB import DB
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.models.pydantic.Playlist import Playlist
from src.utils.spotify_util import NicheTrack
from src.auth.SpotifyUser import spotify_user

from typing import List, TypedDict
from src.utils.spotify_util import (
    extract_id
)
class Artists(TypedDict):
    artist_id: str
    artist_name: str
    genres: list[str]

def get_playlist_tracks(playlist_link: str) -> List[NicheTrack]:
    """
    Retrieves all tracks and associated artist information from a Spotify playlist.

    Args:
        playlist_link (str): The URL to the Spotify playlist.

    Returns:
        List[Dict]: A list of dictionaries, each containing track and artist information.
                    Returns an empty list if no tracks are found or an error occurs.
    """
    # Step 1: Extract Playlist ID from the URL
    playlist_id = extract_id(playlist_link, 'playlist')
    if not playlist_id:
        print("Invalid Spotify playlist link.")
        return []

    
    # Step 2: Retrieve All Tracks from the Playlist
    try:
        tracks = spotify_user.fetch_all_playlist_tracks(playlist_id)
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

    if not tracks:
        print("The playlist contains no tracks.")
        return []

    # Step 5: Prepare Data for Frontend
    playlist_data: list = []
    for track in tracks:
        # Safely retrieve nested dictionary values using .get() with default empty dictionaries or values
        track_data    = track.get('track', {})
        external_urls = track_data.get('external_urls', {})
        artist_data   = track_data.get('artists', [{}])[0]

        track_info: NicheTrack = {
            'track'      : track_data.get('name', 'Unknown Track Name'),
            'spotify_url': external_urls.get('spotify', ''),
            'spotify_uri': track_data.get('uri', ''),
            'artist'     : artist_data.get('name', 'Unknown Artist'),
            'artist_id'  : artist_data.get('id', '')
        }

        playlist_data.append(track_info)

    return(playlist_data)


def get_generated_playlists() -> list[Playlist]:
    """Get all playlists a user has generated

    Returns:
        list[Playlist]: The playlists
    """
    
    return(PlaylistDAO(DB()).read_by_user(user_id=spotify_user.oid))

if __name__ == '__main__':
    print(len(get_generated_playlists()))
    print(get_playlist_tracks('https://open.spotify.com/playlist/5GnqL4E7E3c28zesV9jnPr'))