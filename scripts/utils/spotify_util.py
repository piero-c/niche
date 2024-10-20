from rapidfuzz import fuzz

SpotifyArtist             = dict[str, any]
SpotifyTrack              = dict[str, any]
SpotifyArtistID           = str
SpotifyGenreInterestCount = dict[str, int|float]

SPOTIFY_MAX_LIMIT_PAGINATION = 50

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

def get_top_matching_track(track_name: str, artist_name: str, tracks: list[SpotifyTrack], threshold: int) -> str:
        # Initialize variables to track the best match
        best_match = None
        highest_score = 0

        # Iterate through the search results to find the best fuzzy match
        for track in tracks:
            name = track.get('name', '').lower()
            artist = track.get('artists', [{}])[0].get('name', '').lower()

            # Compute similarity scores for track name and artist
            name_score = fuzz.ratio(track_name.lower(), name)
            artist_score = fuzz.ratio(artist_name.lower(), artist)

            # Calculate an overall score
            overall_score = (name_score * 0.3) + (artist_score * 0.7)

            # Update the best match if this track has a higher score
            if overall_score > highest_score:
                highest_score = overall_score
                best_match = track

        if best_match and highest_score >= threshold:
            return(best_match)
        else:
            raise Exception(f"No suitable Spotify track found for '{track_name}' by '{artist_name}'.")
