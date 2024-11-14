import time

from src.services.playlist_maker.NicheTrackFinder          import NicheTrackFinder
from src.services.playlist_maker.utils.artists_count_check import likely_under_count_playlist
from src.services._shared_classes.PlaylistRequest          import PlaylistRequest, Language, NicheLevel
from src.services._shared_classes.Playlist                 import Playlist

from src.auth.SpotifyUser import spotify_user

from config.personal_init import token

def do(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> str:
    """Generate the playlist based on the request params, return the url

    Args:
        year_min (int): Minimum year for songs to be made in (not in use)
        language (Language): The language of the songs
        niche_level (NicheLevel): Level of niche-ness
        sec_min (int): Min number of seconds for songs
        sec_max (int): Max number of seconds for songs
        genre (str): Genre for the songs to be in

    Returns:
        str: Playlist url
    """
    t0     = time.time()
    req    = PlaylistRequest(year_min, language, niche_level, sec_min, sec_max, genre, True)
    finder = NicheTrackFinder(req)
    songs  = finder.find_niche_tracks()
    pl     = Playlist(songs, req)
    t1     = time.time()
    total  = (t1-t0)/60
    pl.add_generated_time(total)
    print(f'TOTAL MINUTES RUN: {total}')

    print(pl.url)
    return (pl.url)

def playlist_likely_undersized(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> bool:
    """Will the playlist likely be undersized? (And hence throw an error)"""
    return(likely_under_count_playlist(PlaylistRequest(year_min, language, niche_level, sec_min, sec_max, genre, False)))

if __name__ == '__main__':
    spotify_user.initialize(token)
    do(0, Language.ANY, NicheLevel.ONLY_KINDA, 120, 10000, 'jazz')
