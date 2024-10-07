import spotipy

class SpotifySearch:
    """Object for searching spotify at a non-user-specific granularity
    """
    def __init__(self, user: spotipy.Spotify) -> None:
        """Init

        Args:
            user (spotipy.Spotify): The authenticated user
        """
        self.user = user
    
    def get_genres_from_artist_ids(self, artist_ids: list[str], artist_cache: dict[str, dict] = {}) -> dict[str, int]:
        """Collect a list of genre instances from a list of artist ids

        Args:
            artist_ids (list[str]): List of artist ids to check.
            artist_cache (dict[str, dict], optional): Dict of artist ids to artist objects. Defaults to {}.

        Returns:
            dict[str, int]: key: genre, val: instance count from artists
        """
        genres = {}
        for artist_id in artist_ids:
            if artist_id not in artist_cache:
                artist_details = self.user.artist(artist_id)
                artist_cache[artist_id] = artist_details
            else:
                artist_details = artist_cache[artist_id]
            for genre in artist_details['genres']:
                genres[genre] = genres.get(genre, 0) + 1
        return genres
