from src.db.DB import DB
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.auth.SpotifyUser import SpotifyUser
from src.models.pydantic.Playlist import Playlist
from src.utils.util import convert_ms_to_s

from typing import List, TypedDict
from src.utils.spotify_util import (
    get_artists_ids_and_genres_as_dict,
    get_artist_ids_from_tracks,
    extract_id
)
class Artists(TypedDict):
    artist_id: str
    artist_name: str
    genres: list[str]

class PlaylistTracks(TypedDict):
    track_name: str
    album_name: str
    duration_s: float
    spotify_track_url: str
    artists: Artists

def get_playlist_tracks(playlist_link: str, user: SpotifyUser) -> List[PlaylistTracks]:
    """
    Retrieves all tracks and associated artist information from a Spotify playlist.

    Args:
        playlist_link (str): The URL to the Spotify playlist.
        user (SpotifyUser): An instance of SpotifyUser representing the authenticated user.

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
        tracks = user.fetch_all_playlist_tracks(playlist_id)
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

    if not tracks:
        print("The playlist contains no tracks.")
        return []

    # Step 3: Gather Artist IDs from Tracks
    artist_ids = get_artist_ids_from_tracks(tracks)

    # Step 4: Retrieve Artists' Genres
    artists = [user.get_spotify_artist_by_id(artist_id) for artist_id in list(artist_ids)]
    artists_info = get_artists_ids_and_genres_as_dict(artists)

    # Step 5: Prepare Data for Frontend
    playlist_data = []
    for track in tracks:
        # Safely retrieve nested dictionary values using .get() with default empty dictionaries or values
        track_data = track.get('track', {})
        album_data = track_data.get('album', {})
        external_urls = track_data.get('external_urls', {})
        artists_list = track_data.get('artists', [])

        track_info = {
            'track_name': track_data.get('name', 'Unknown Track Name'),
            'album_name': album_data.get('name', 'Unknown Album Name'),
            'duration_s': convert_ms_to_s(track_data.get('duration_ms', 0)),
            'spotify_track_url': external_urls.get('spotify', ''),
            'artists': []
        }

        for artist in artists_list:
            artist_id = artist.get('id', '')
            artist_name = artist.get('name', 'Unknown Artist')
            genres = artists_info.get(artist_id, [])

            artist_info = {
                'artist_id': artist_id,
                'artist_name': artist_name,
                'genres': genres
            }

            track_info['artists'].append(artist_info)

        playlist_data.append(track_info)

    return(playlist_data)


def get_generated_playlists(user: SpotifyUser) -> list[Playlist]:
    """Get all playlists a user has generated

    Args:
        user (SpotifyUser): The user

    Returns:
        list[Playlist]: The playlists
    """
    return(PlaylistDAO(DB()).read_by_user(user_id=user.oid))

if __name__ == '__main__':
    print(len(get_generated_playlists(SpotifyUser())))
    print(get_playlist_tracks('https://open.spotify.com/playlist/5GnqL4E7E3c28zesV9jnPr', SpotifyUser()))