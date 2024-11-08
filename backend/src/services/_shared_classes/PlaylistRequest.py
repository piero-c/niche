from src.utils.util import Language, NicheLevel, NICHEMAP, LANGMAP
from src.db.DB import DB
from src.db.DAOs.RequestsDAO import RequestDAO
from src.models.pydantic.Request import Request, Params
from typing import TypedDict
from src.utils.util import NICHE_APP_URL
from src.services.genre_handling.valid_genres import genres as valid_genres
from src.auth.SpotifyUser import spotify_user
class PlaylistInfo(TypedDict):
    """Playlist info obj

    Args:
        TypedDict
    """
    name       : str
    description: str

# Dictionary for maximums and minimums for "nicheness"
#  All must apply EXCEPT lastfm playcount and listeners, where EITHER may apply
# All values go up by multiples of 3, except spotify followers min
niche_level_map = {
    NicheLevel.VERY: {
        "lastfm_listeners_min" : 1_000,
        "lastfm_listeners_max" : 50_000,
        "lastfm_playcount_min" : 10_000,
        "lastfm_playcount_max" : 500_000,
        "spotify_followers_min": 100,
        "spotify_followers_max": 5_000
    },
    NicheLevel.MODERATELY: {
        "lastfm_listeners_min" : 3_000,
        "lastfm_listeners_max" : 150_000,
        "lastfm_playcount_min" : 30_000,
        "lastfm_playcount_max" : 1_500_000,
        "spotify_followers_min": 1_000,
        "spotify_followers_max": 15_000
    },
    NicheLevel.ONLY_KINDA: {
        "lastfm_listeners_min" : 9_000,
        "lastfm_listeners_max" : 450_000,
        "lastfm_playcount_min" : 90_000,
        "lastfm_playcount_max" : 4_500_000,
        "spotify_followers_min": 10_000,
        "spotify_followers_max": 45_000
    }
}

class PlaylistRequest:
    """Playlist Request

    Attributes:
        songs_min_year_created
        songs_length_min_secs 
        songs_length_max_secs 
        language              
        genre  
        lastfm_listeners_max 
        lastfm_listeners_min 
        lastfm_playcount_max 
        lastfm_playcount_min 
        spotify_followers_max
        spotify_followers_min               
        niche_level
        lastfm_likeness_min 
        playlist_length     
        user_oid
        oid
            Requires call: add_db_entry
        in_db
    """
    def __init__(self, songs_min_year_created: int, language: Language, niche_level: NicheLevel, 
                    songs_length_min_secs: int, songs_length_max_secs: int, genre: str, add_to_db: bool = True) -> None:
        """Initialize the request

        Args:
            songs_min_year_created (int): Min year for the songs to be created in
            language (Language)         : Language for the songs to be in
            niche_level (NicheLevel)    : Level of nicheness
            songs_length_min_secs (int) : Min length of given song
            songs_length_max_secs (int) : Max length of given song
            genre (str)                 : requested genre
            add_to_db (bool, optional)  : Add the playlist to the db?. Default to true
        """
        assert(genre in valid_genres()) # Genre is spotify genre

        

        self.songs_min_year_created = songs_min_year_created
        self.songs_length_min_secs  = songs_length_min_secs
        self.songs_length_max_secs  = songs_length_max_secs
        self.language               = language # This stays as an enum
        self.genre                  = genre
        self.niche_level            = niche_level
        self.user_oid               = spotify_user.oid

        # Based on the niche level set mins and maxes
        self.lastfm_listeners_max  = niche_level_map[niche_level]["lastfm_listeners_max"]
        self.lastfm_listeners_min  = niche_level_map[niche_level]["lastfm_listeners_min"]
        self.lastfm_playcount_max  = niche_level_map[niche_level]["lastfm_playcount_max"]
        self.lastfm_playcount_min  = niche_level_map[niche_level]["lastfm_playcount_min"]
        self.spotify_followers_max = niche_level_map[niche_level]["spotify_followers_max"]
        self.spotify_followers_min = niche_level_map[niche_level]["spotify_followers_min"]

        # Hardcoded vals
        self.lastfm_likeness_min  = 3.5
        self.playlist_length      = 20

        #self.playlist_length = 1

        self.in_db = False
        if (add_to_db):
            self.add_db_entry()

    def add_db_entry(self) -> None:
        if (self.in_db):
            return (None)
        db = DB()
        dao = RequestDAO(db)

        # Make the request
        db_entry = dao.create(
            Request(
                user = self.user_oid,
                params = Params(
                    songs_min_year_created=self.songs_min_year_created,
                    songs_length_min_secs=self.songs_length_min_secs,
                    songs_length_max_secs=self.songs_length_max_secs,
                    language=LANGMAP.inv.get(self.language, {}),
                    genre=self.genre,
                    niche_level=NICHEMAP.inv.get(self.niche_level, {})
                )
            )
        )

        self.oid = db_entry.inserted_id

        self.in_db = True
        return(None)

    def get_playlist_info(self) -> PlaylistInfo:
        """Get the info for the playlist

        Returns:
            PlaylistInfo: the info
        """
        return({
            'name': f'Niche {self.genre} Songs',
            'description': f'Courtesy of the niche app :) ({NICHE_APP_URL})'
        })
