from utils.util import strcomp

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

def get_artists_ids_and_genres_from_artists(artists: list[SpotifyArtist]) -> tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]:
    """From a list of artist objects, get ids and genres.

    Args:
        artists (list[SpotifyArtist]): List of Spotify Artists.

    Returns:
        tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]: (set[artist ids], dict[genre: number of instances in artists]).
    """
    artist_ids = get_artist_ids_from_artists(artists)
    genres = {}
    for artist in artists:
        for genre in artist['genres']:
            # Add one to genre or create genre and add one
            genres[genre] = genres.get(genre, 0) + 1
    return(artist_ids, genres)

def get_artist_ids_from_tracks(tracks: list[SpotifyTrack]) -> set[SpotifyArtistID]:
    """From a list of track objects, get the artist ids.

    Args:
        tracks (list[SpotifyTrack]): List of Spotify Tracks.

    Returns:
        set[SpotifyArtistID]: Set of artist ids.
    """
    artist_ids = set()
    for track in tracks:
        for artist in track['artists']:
            artist_ids.add(artist['id'])
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