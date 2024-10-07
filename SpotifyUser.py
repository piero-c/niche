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

    def _get_items(self, type: str, num_items: int|str = 'all', time_range: str = 'medium_term') -> list[dict]:
        """Get specified items for the user

        Args:
            type (str): Which items to get. Must be one of "followed_artists", "top_artists", "top_tracks"
            num_items (int, optional): The number of items to collect. Must be one of (int > 0 <= 50) or "all". Defaults to 'all'.
            time_range (str, optional): The time range if applicable. Must be one of 'short_term', 'medium_term', or 'long_term'. 
                Defaults to 'medium_term'.

        Returns:
            list[dict]: A list of the items requested
        """
        assert((num_items == 'all') or ((num_items > 0) and (num_items <= 50)) )
        assert((time_range == 'short_term') or (time_range == 'medium_term') or (time_range == 'long_term'))
        assert((type == "followed_artists") or (type == "top_artists") or (type == "top_tracks"))

        # Generate limit and set bool for all items
        if num_items == "all":
            limit = 50
            all_items = True
        else:
            limit = num_items
            all_items = False

        items = []

        # Get initial items
        if (type == "followed_artists"):
            results = self.user.current_user_followed_artists(limit = limit)
            items.extend(results['artists']['items'])
        elif (type == "top_artists"):
            results = self.user.current_user_top_artists(limit = limit, time_range = time_range)
            items.extend(results['items'])
        elif (type == "top_tracks"):
            results = self.user.current_user_top_tracks(limit = limit, time_range = time_range)
            items.extend(results['items'])
        
        # If all items, iterate the rest of the objects
        if (all_items):
            if ((type == "followed_artists")):
                while results['artists']['next']:
                    results = self.user.next(results['artists'])
                    items.extend(results['artists']['items'])
            else:
                while results['next']:
                    results = self.user.next(results)
                    items.extend(results['items'])

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
        # Get followed artists
        followed_artists = self._get_items(type = 'followed_artists')

        print("1")
        # Get artist ids 
        artist_ids_top_artists, genres_top_artists = get_artists_ids_and_genres_from_artists(top_artists)
        artist_ids_top_tracks = get_artist_ids_from_tracks(top_tracks)
        artist_ids_followed_artists = get_artist_ids_from_artists(followed_artists)

        print("2")

        # Remove artist IDs already in top artists for track genre checking
        #   We do this second because we already have genres from top artists
        artist_ids_top_tracks_only = artist_ids_top_tracks - artist_ids_top_artists
        # Remove artist IDs already in top artists for followed artist genre checking
        #   We do this last because we weight artists that are followed but don't show up in top tracks or artists the least
        artist_ids_followed_only = artist_ids_followed_artists - artist_ids_top_artists - artist_ids_top_tracks_only

        # Get genres from track artists
        genres_top_tracks = search.get_genres_from_artist_ids(artist_ids_top_tracks_only)
        # Get genres from followed artists
        genres_followed_artists = search.get_genres_from_artist_ids(artist_ids_followed_only)

        print("3")

        # Merge genres with appropriate weights
        genre_dict = merge_dicts_with_weight([genres_top_artists, genres_top_tracks, genres_followed_artists], [1, 1, 0.5])

        barely_enjoyed_genres = []

        # Remove genres with a weight < 2
        for key, val in genre_dict.items():
            if val < 2:
                barely_enjoyed_genres.append(key)
        for genre in barely_enjoyed_genres:
            del genre_dict[genre]

        # Return the genre dictionary
        return genre_dict
