from utils.util import strcomp

from typing import Optional
from urllib.parse import urlparse, parse_qs
import re

SpotifyArtist             = dict[str, any]
SpotifyTrack              = dict[str, any]
SpotifyArtistID           = str
SpotifyGenreInterestCount = dict[str, int|float]

SPOTIFY_MAX_LIMIT_PAGINATION = 50

def get_artist_ids_from_artists(artists: list[SpotifyArtist]) -> set[SpotifyArtistID]:
    """Get artist ids from list of artist objects.

    Args:
        artists (list[SpotifyArtist]): List of artist objects.

    Returns:
        set[SpotifyArtistID]: Set of artist ids.
    """
    return(set(artist['id'] for artist in artists))

def get_artists_ids_and_genres_as_dict(
    artists: list[SpotifyArtist]
) -> dict[SpotifyArtistID: list[str]]:
    """
    From a list of artist objects, get a dict containing artist IDs and their genres.

    Args:
        artists (List[SpotifyArtist]): List of Spotify Artist objects.

    Returns:
        dict[SpotifyArtistID: list[str]]: 
            A dict of artist id to list of genres
    """
    artist_genres_dict = {}
    for artist in artists:
        artist_id = artist.get('id')
        artist_genres = artist.get('genres', [])
        if artist_id:
            artist_genres_dict[artist_id] = artist_genres
    return(artist_genres_dict)

def get_artists_ids_and_genres_from_artists(artists: list[SpotifyArtist]) -> tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]:
    """From a list of artist objects, get ids and genres.

    Args:
        artists (list[SpotifyArtist]): List of Spotify Artists.

    Returns:
        tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]: (set[artist ids], dict[genre: number of instances in artists]).
    """
    artist_genres = get_artists_ids_and_genres_as_dict(artists)
    
    artist_ids: set[SpotifyArtistID] = set()
    genres_count: SpotifyGenreInterestCount = {}
    
    for artist_id, artist_genres in artist_genres.values():
        artist_ids.add(artist_id)
        for genre in artist_genres:
            genres_count[genre] = genres_count.get(genre, 0) + 1
    
    return (artist_ids, genres_count)

def get_artist_ids_from_tracks(tracks: list[SpotifyTrack]) -> set[SpotifyArtistID]:
    """From a list of track objects, get the artist ids.

    Args:
        tracks (list[SpotifyTrack]): List of Spotify Tracks.

    Returns:
        set[SpotifyArtistID]: Set of artist ids.
    """
    artist_ids = set()
    for track in tracks:
        for artist in track.get('track', {}).get('artists', {}):
            artist_ids.add(artist.get('id'))
    return(artist_ids)

def find_exact_match(tracks: list[SpotifyTrack], name: str, artist: str) -> SpotifyTrack:
    """
    Finds an exact match for a track name and artist within a list of SpotifyTrack dictionaries.

    Args:
        tracks (List[SpotifyTrack]): A list of SpotifyTrack dictionaries returned by Spotify search.
        name (str): The exact name of the song to match.
        artist (str): The name of an artist to be present in the track's artists list.

    Returns:
        SpotifyTrack: The SpotifyTrack dictionary if an exact match is found; otherwise, None.
    """
    for track in tracks:
        # Validate that 'name' and 'artists' exist in the track
        track_name = track.get('name')
        track_artists = track.get('artists')

        if ((not track_name) or (not track_artists)):
            continue  # Skip tracks with missing information

        # Check if track name matches exactly using strcomp
        if (strcomp(track_name, name)):
            # Extract and normalize artist names
            artist_names = [a.get('name', '') for a in track_artists]
            # Check if the specified artist is among the track's artists using strcomp
            for a_name in artist_names:
                if (strcomp(a_name, artist)):
                    return (track)  # Exact match found
    return (None)  # No exact match found

def extract_id(playlist_link: str, type: str) -> Optional[str]:
    """
    Extracts the Spotify playlist ID from a playlist URL.

    Args:
        playlist_link (str): The URL to the Spotify playlist.
        type (str): The type of url

    Returns:
        Optional[str]: The playlist ID if extraction is successful; otherwise, None.
    """
    # Spotify playlist URL patterns
    patterns = [
        rf"https?://open\.spotify\.com/{type}/([a-zA-Z0-9]+)",
        rf"spotify:{type}:([a-zA-Z0-9]+)"
    ]

    for pattern in patterns:
        match = re.match(pattern, playlist_link)
        if match:
            return match.group(1)

    # Attempt to parse URL for query parameters (e.g., share links)
    parsed_url = urlparse(playlist_link)
    query_params = parse_qs(parsed_url.query)
    if 'list' in query_params:
        return query_params['list'][0]

    return None
