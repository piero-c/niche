SpotifyArtist             = dict[str, any]
SpotifyTrack              = dict[str, any]
SpotifyArtistID           = str
SpotifyGenreInterestCount = dict[str, int|float]

def get_artists_ids_and_genres_from_artists(artists: list[SpotifyArtist]) -> tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]:
    """From a list of artist objects, get ids and genres.

    Args:
        artists (list[SpotifyArtist]): List of Spotify Artists.

    Returns:
        tuple[set[SpotifyArtistID], SpotifyGenreInterestCount]: (set[artist ids], dict[genre: number of instances in artists]).
    """
    artist_ids = set()
    genres = {}
    for artist in artists:
        # Get id
        artist_ids.add(artist['id'])
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

def get_artist_ids_from_artists(artists: list[SpotifyArtist]) -> set[SpotifyArtistID]:
    """Get artist ids from list of artist objects.

    Args:
        artists (list[SpotifyArtist]): List of artist objects.

    Returns:
        set[SpotifyArtistID]: Set of artist ids.
    """
    return(set(artist['id'] for artist in artists))
