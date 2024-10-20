from enum import Enum

# Enumerations for request
Language       = Enum('Language', ['ANY', 'ENGLISH_ONLY'])
NicheLevel     = Enum('NicheLevel', ['VERY', 'MODERATELY', 'ONLY_KINDA'])

# Dictionary for maximums and minimums for "nicheness"
#  All must apply EXCEPT lastfm playcount and listeners, where EITHER may apply
# All values go up by multiples of 3, except spotify followers min
# TODO - and edit request to change to somethind else (and length of playlist? idk maybe just set restrictions on the params based on certain stuff)
# TODO - Then go to track fuzzy search
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
        TODO
    """
    def __init__(self, songs_min_year_created: int, language: Language, niche_level: NicheLevel, 
                    songs_length_min_secs: int, songs_length_max_secs: int, genre: str) -> None:
        """_summary_

        Args:
            songs_min_year_created (int): _description_
            language (Language): _description_
            playlist_length (PlaylistLength): _description_
            niche_level (NicheLevel): _description_
            songs_length_min_secs (int): _description_
            songs_length_max_secs (int): _description_
            max_songs_per_artist (int): _description_
            genre (str): _description_
        """
        self.songs_min_year_created = songs_min_year_created
        self.songs_length_min_secs  = songs_length_min_secs
        self.songs_length_max_secs  = songs_length_max_secs
        self.language               = language # This stays as an enum
        self.genre                  = genre
        self.niche_level            = niche_level

        self.lastfm_listeners_max  = niche_level_map[niche_level]["lastfm_listeners_max"]
        self.lastfm_listeners_min  = niche_level_map[niche_level]["lastfm_listeners_min"]
        self.lastfm_playcount_max  = niche_level_map[niche_level]["lastfm_playcount_max"]
        self.lastfm_playcount_min  = niche_level_map[niche_level]["lastfm_playcount_min"]
        self.spotify_followers_max = niche_level_map[niche_level]["spotify_followers_max"]
        self.spotify_followers_min = niche_level_map[niche_level]["spotify_followers_min"]

        # Hardcoded vals
        self.lastfm_likeness_min  = 4
        self.playlist_length      = 20
        self.max_songs_per_artist = 1
