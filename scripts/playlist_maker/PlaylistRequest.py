# Module for the playlist request
from enum import Enum

Language       = Enum('Language', ['ANY', 'ENGLISH_ONLY'])
PlaylistLength = Enum('PlaylistLength', ['SHORT', 'MEDIUM', 'LONG'])
NicheLevel     = Enum('NicheLevel', ['VERY', 'MODERATELY', 'ONLY_KINDA'])

class PlaylistRequest:
    def __init__(self, songs_min_year_created: int, language: Language, playlist_length: PlaylistLength, niche_level: NicheLevel, 
                    songs_length_min_secs: int, songs_length_max_secs: int, max_songs_per_artist: int, genre: str) -> None:
        self.songs_min_year_created = songs_min_year_created
        self.songs_length_min_secs  = songs_length_min_secs
        self.songs_length_max_secs  = songs_length_max_secs
        self.max_songs_per_artist   = max_songs_per_artist
        self.language               = language # This stays as an enum
        self.genre                  = genre
        # Set playlist length
        if (playlist_length == PlaylistLength.SHORT):
            self.playlist_length = 20 # Roughly 1 hour
        elif (playlist_length == PlaylistLength.MEDIUM):
            self.playlist_length = 60 # Roughly 3 hours
        elif (playlist_length == playlist_length.LONG):
            self.playlist_length = 120 # Roughly 6 hours
        # Set niche level
        if (niche_level == NicheLevel.VERY):
            self.lastfm_playcount_max = 3000
        elif (niche_level == NicheLevel.MODERATELY):
            self.lastfm_playcount_max = 7000
        elif (niche_level == NicheLevel.ONLY_KINDA):
            self.lastfm_playcount_max = 25000

        # Hardcoded vals
        self.lastfm_playcount_min   = 100
        self.lastfm_likeness_max    = 5
        self.spotify_popularity_max = 50

