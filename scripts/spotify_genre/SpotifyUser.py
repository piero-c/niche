from spotipy.oauth2 import SpotifyOAuth
import spotipy

from scripts.spotify_genre.spotify_util import get_artists_ids_and_genres_from_artists, get_artist_ids_from_tracks, get_artist_ids_from_artists
from scripts.util import merge_dicts_with_weight, load_env

class SpotifyUser:
    """
    Spotify Authenticated User Object

    Attributes:

    """
    def __init__(self) -> None:
        """Creates a Spotify User.
        """
        env = load_env()
        # Initialize Spotipy with SpotifyOAuth
        self.user = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id     = env['SPOTIFY_CLIENT_ID'],
            client_secret = env['SPOTIFY_CLIENT_SECRET'],
            redirect_uri  = env['SPOTIFY_REDIRECT_URI'],
            scope         = env['SCOPE'],
            cache_path    = env['CACHE_PATH']
        ))

        # Collect identifying information from user
        self.name = self.user.current_user()['display_name']
        self.id   = self.user.current_user()['id']

    def _get_items(self, type: str, num_items: int = 200, time_range: str = 'medium_term') -> list[dict]:
        """Get specified items for the user

        Args:
            type (str): Which items to get. Must be one of "top_artists", "top_tracks"
            num_items (int, optional): The number of items to collect. Must be > 0, <= 200. Defaults to 200
            time_range (str, optional): The time range. Must be one of 'short_term', 'medium_term', or 'long_term'. 
                Defaults to 'medium_term'.

        Returns:
            list[dict]: A list of the items requested
        """
        assert((num_items > 0) and (num_items <= 200))
        assert((time_range == 'short_term') or (time_range == 'medium_term') or (time_range == 'long_term'))
        assert((type == "top_artists") or (type == "top_tracks"))

        # TODO - Refactor (DRY)
        items = []
        offset = 0
        while True:
            # Generate limit and set bool for all items
            limit = (50 if (num_items >= 50) else num_items)

            # Get initial items
            if (type == "top_artists"):
                results = self.user.current_user_top_artists(limit = limit, time_range = time_range, offset = offset)
            elif (type == "top_tracks"):
                results = self.user.current_user_top_tracks(limit = limit, time_range = time_range, offset = offset)

            items.extend(results['items'])
            num_items -= limit
            offset += limit

            if (not ((results['next']) and (num_items > 0))):
                break

        return(items)
    
    def search_get_genres_from_artist_ids(self, artist_ids: list[str], artist_cache: dict[str, dict] = {}) -> dict[str, int]:
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
    
    def get_top_genres(self) -> dict[str, int|float]:
        # TODO - Add args for all method functions and for this function and add pydoc

        # Get top artists
        top_artists = self._get_items(type = 'top_artists')
        # Get top tracks
        top_tracks = self._get_items(type = 'top_tracks')

        # Get artist ids 
        artist_ids_top_artists, genres_top_artists = get_artists_ids_and_genres_from_artists(top_artists)
        artist_ids_top_tracks = get_artist_ids_from_tracks(top_tracks)

        # Remove artist IDs already in top artists for track genre checking
        #   We do this second because we already have genres from top artists
        artist_ids_top_tracks_only = artist_ids_top_tracks - artist_ids_top_artists

        # Get genres from track artists
        genres_top_tracks = self.search_get_genres_from_artist_ids(artist_ids_top_tracks_only)

        # Merge genres with appropriate weights
        genre_dict = merge_dicts_with_weight([genres_top_artists, genres_top_tracks], [1, 1])

        barely_enjoyed_genres = []

        # Remove genres with a weight < 2
        for key, val in genre_dict.items():
            if val < 2:
                barely_enjoyed_genres.append(key)
        for genre in barely_enjoyed_genres:
            del genre_dict[genre]

        # Return the genre dictionary
        return genre_dict
