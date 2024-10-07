def get_artists_ids_and_genres_from_artists(artists: list[dict]) -> tuple[set[str], dict[str, int]]:
    """From a list of artist objects, get ids and genres.

    Args:
        artists (list[dict]): List of dicts of artist objects.

    Returns:
        tuple[set[str], dict[str, int]]: (set[artist ids], dict[genre: number of instances in artists].)
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

def get_artist_ids_from_tracks(tracks: list[dict]) -> set[str]:
    """From a list of track objects, get the artist ids

    Args:
        tracks (list[dict]): List of track objects

    Returns:
        set[str]: Set of artist ids
    """
    artist_ids = set()
    for track in tracks:
        for artist in track['artists']:
            artist_ids.add(artist['id'])
    return(artist_ids)

def get_artist_ids_from_artists(artists: list[dict]) -> set:
    """Get artist ids from list of artist objects

    Args:
        artists (list[dict]): List of artist objects

    Returns:
        set: Set of artist ids
    """
    return(set(artist['id'] for artist in artists))
