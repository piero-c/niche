from src.utils.spotify_util import get_artists_ids_and_genres_from_artists, get_artist_ids_from_tracks, SpotifyArtist, SpotifyTrack, SpotifyArtistID, SpotifyGenreInterestCount, SPOTIFY_MAX_LIMIT_PAGINATION
from src.utils.util import load_env, sleep, RequestType, filter_low_count_entries, merge_dicts_with_weight
from typing import Optional, Type, ClassVar
import spotipy
from spotipy import SpotifyOAuth
from src.models.pydantic.BaseSchema import PyObjectId
from src.models.pydantic.User import User
from src.db.DB import DB
from src.db.DAOs.UsersDAO import UserDAO
from PIL import Image
import io
import base64

from src.utils.logger import logger
import requests
class SpotifyUser:
    """Spotify-Authenticated User

    Raises:
        Exception: If more than one user is defined
    """
    _instance: ClassVar[Optional['SpotifyUser']] = None

    client: spotipy.Spotify
    user  : dict
    name  : str
    id    : str
    oid   : PyObjectId

    def __new__(cls: Type['SpotifyUser']) -> 'SpotifyUser':
        """Create the user

        Args:
            cls (Type[&#39;SpotifyUser&#39;]): SpotifyUser

        Returns:
            SpotifyUser: The user, authenticated
        """
        if(cls._instance is None):
            env = load_env()
            cls._instance = super(SpotifyUser, cls).__new__(cls)
            ## BEGIN REQUEST ##
            cls._instance.client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id     = env['SPOTIFY_CLIENT_ID'],
                client_secret = env['SPOTIFY_CLIENT_SECRET'],
                redirect_uri  = env['SPOTIFY_REDIRECT_URI'],
                scope         = env['SCOPE'],
                cache_path    = env['CACHE_PATH']
            ))
            sleep(RequestType.SPOTIFY)
            ## END REQUEST ##

            cls._instance.user = cls._instance.client.current_user()
            cls._instance.name = cls._instance.user['display_name']
            cls._instance.id   = cls._instance.user['id']
            
            db = DB()
            dao = UserDAO(db)
            db_entry = dao.create_or_update_by_spotify_id(
                User(
                    display_name=cls._instance.name,
                    spotify_id=cls._instance.id
                )
            )

            cls._instance.oid  = db_entry.id

        return(cls._instance)
    
    ## GENERAL SEARCH ##
    
    def get_spotify_tracks_direct(self, name: str, artist: str) -> list[SpotifyTrack]:
        """Search for top 10 matching spotify tracks via direct search

        Args:
            name (str): Song name
            artist (str): Artist Name

        Raises:
            Exception: If no tracks are found

        Returns:
            list[SpotifyTrack]: A list of the top 10 matching tracks
        """
        # Construct the search query with specific field filters
        q = f"track:{name} artist:{artist}"

        ## BEGIN REQUEST ##
        # Perform the search on Spotify for the track with a limit of 10
        search_results = self.client.search(q=q, type='track', limit=10)
        sleep(RequestType.SPOTIFY)  # Respect API rate limits
        ## END REQUEST ##

        # Extract the list of track items from the search results
        spotify_tracks = search_results.get('tracks', {}).get('items', [])
        if(not spotify_tracks):
            raise Exception(f"No Spotify tracks found for {name} by {artist}.")

        return(spotify_tracks)

    def get_spotify_artist_by_id(self, id: str) -> SpotifyArtist:
        """Get a spotify artist object by their spotify id

        Args:
            id (str): Spotify id

        Returns:
            SpotifyArtist: The artist as returned by Spotify
        """
        ## BEGIN REQUEST ##
        # Retrieve the full artist object from Spotify using the artist ID
        spotify_artist = self.client.artist(id)
        sleep(RequestType.SPOTIFY)
        ## END REQUEST ##

        return(spotify_artist)

    ## USER SPECIFIC ITEMS ##

    def _get_items(self, type: str, num_items: int = 200, time_range: str = 'medium_term') -> list[SpotifyArtist|SpotifyTrack]:
        """Get specified items for the user.

        Args:
            type (str): Which items to get. Must be one of "top_artists", "top_tracks".
            num_items (int, optional): The number of items to collect. Must be > 0, <= 200. Defaults to 200.
            time_range (str, optional): The time range. Must be one of 'short_term', 'medium_term', or 'long_term'. 
                Defaults to 'medium_term'.

        Returns:
            list[SpotifyArtist|SpotifyTrack]: A list of the items requested.
        """
        assert((num_items > 0) and (num_items <= 200))
        assert((time_range == 'short_term') or (time_range == 'medium_term') or (time_range == 'long_term'))
        assert((type == "top_artists") or (type == "top_tracks"))

        items = []
        offset = 0
        while True:
            # Generate limit
            limit = (SPOTIFY_MAX_LIMIT_PAGINATION if(num_items >= SPOTIFY_MAX_LIMIT_PAGINATION) else num_items)

            # Get initial items
            if(type == "top_artists"):
                results = self.client.current_user_top_artists(limit = limit, time_range = time_range, offset = offset)
            elif(type == "top_tracks"):
                results = self.client.current_user_top_tracks(limit = limit, time_range = time_range, offset = offset)

            items.extend(results['items'])
            num_items -= limit
            offset += limit

            if(not ((results['next']) and (num_items > 0))):
                break

        return(items)
    
    def get_genres_from_artist_ids(self, artist_ids: list[SpotifyArtistID], artist_cache: dict[str, dict] = {}) -> SpotifyGenreInterestCount:
        """Get a genre count from a list of artist IDs. Each artist (usually) has multiple genres, all of which are counted equally

        Args:
            artist_ids (list[SpotifyArtistID]): The Spotify IDs
            artist_cache (dict[str, dict], optional): I'm too scared to remove this. Defaults to {}.

        Returns:
            SpotifyGenreInterestCount: Genre: Count
        """
        genres = {}
        for artist_id in artist_ids:
            if artist_id not in artist_cache:
                artist_details = self.client.artist(artist_id)
                artist_cache[artist_id] = artist_details
            else:
                artist_details = artist_cache[artist_id]
            for genre in artist_details['genres']:
                genres[genre] = genres.get(genre, 0) + 1
        return(genres)
    
    def get_top_genres(self) -> SpotifyGenreInterestCount:
        """Get the User's top genres

        Returns:
            SpotifyGenreInterestCount: Genre: Count

        Post:
            Returns genres which were derived from one or more items, only those with count above 2
        """
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
        genres_top_tracks = self.get_genres_from_artist_ids(artist_ids_top_tracks_only)

        # Merge genres with appropriate weights
        genre_dict = merge_dicts_with_weight([genres_top_artists, genres_top_tracks], [1, 1])

        # Return the genre dictionary
        return(filter_low_count_entries(genre_dict, count=2))
    
    # TODO - fetch normal spotify track here
    def fetch_all_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """
        Fetches all tracks from a Spotify playlist, handling pagination.

        Args:
            playlist_id (str): The unique identifier for the Spotify playlist.

        Returns:
            List[dict]: A list of dict objects in the playlist.
        """
        tracks = []
        limit = SPOTIFY_MAX_LIMIT_PAGINATION  # Typically 100
        offset = 0

        while True:
            # BEGIN REQUEST
            response = self.client.playlist_items(
                playlist_id,
                offset=offset,
                limit=limit,
                fields='items(track(id,name,duration_ms,artists(name,id),album(name),external_urls)),next'
            )
            sleep(RequestType.SPOTIFY)
            # END REQUEST

            items = response.get('items', [])
            tracks.extend(items)

            if ((not response.get('next')) or (len(items) < limit)):
                break

            offset += limit

        return (tracks)

    def execute(
        self,
        method_name: str,
        *args,
        **kwargs
    ) -> Optional[any]:
        """_summary_

        Args:
            method_name (str): _description_

        Returns:
            Optional[any]: _description_
        """
        try:
            # Dynamically get the method from the Spotipy client
            method = getattr(self.client, method_name)

            ## BEGIN REQUEST ##
            # Execute the method with provided arguments
            result = method(*args, **kwargs)
            sleep(RequestType.SPOTIFY)
            ## END REQUEST ##

            return(result)
        except AttributeError:
            logger.error(f"The Spotipy client does not have a method named '{method_name}'.")
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"SpotifyException occurred while executing '{method_name}': {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while executing '{method_name}': {e}")
        
        return(None)


    def upload_playlist_cover_image(self, cover_image_path: str) -> None:
        """_summary_

        Args:
            cover_image_path (str): _description_
        """
        # Open the image and convert it to a base64-encoded JPEG
        with Image.open(cover_image_path) as img:
            img = img.convert("RGB")  # Ensure the image is in RGB format
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        try:
            self.client.playlist_upload_cover_image(self.id, image_base64)
        except requests.exceptions.ReadTimeout:
            # Handle the timeout exception as needed
            logger.error("Timeout occurred while uploading the cover image. Please try again later.")



