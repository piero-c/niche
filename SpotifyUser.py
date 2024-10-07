from dotenv import load_dotenv
import os
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from SpotifySearch import SpotifySearch

from spotify_util import get_artists_ids_and_genres_from_artists, get_artist_ids_from_tracks, get_artist_ids_from_artists
from util import merge_dicts_with_weight


def load_env():
    load_dotenv()
    global CLIENT_ID
    global CLIENT_SECRET
    global REDIRECT_URI
    global SCOPE
    global CACHE_PATH

    CLIENT_ID     = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI  = os.getenv('SPOTIFY_REDIRECT_URI')
    SCOPE         = "user-top-read user-follow-read"
    CACHE_PATH    = ".cache"

class SpotifyUser:
    """
    Spotify Authenticated User Object

    Attributes:

    """
    def __init__(self) -> None:
        """Creates a Spotify User.
        """
        load_env()
        # Initialize Spotipy with SpotifyOAuth
        self.user = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id     = CLIENT_ID,
            client_secret = CLIENT_SECRET,
            redirect_uri  = REDIRECT_URI,
            scope         = SCOPE,
            cache_path    = CACHE_PATH
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
    
    def _create_search(self) -> SpotifySearch:
        """Create a Spotify Search object

        Returns:
            SpotifySearch: The spotify search object
        """
        return(SpotifySearch(user = self.user))
    
    def get_top_genres(self) -> dict[str, int|float]:
        # TODO - Add args for all method functions and for this function and add pydoc
        search = self._create_search()

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
        genres_top_tracks = search.get_genres_from_artist_ids(artist_ids_top_tracks_only)

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
