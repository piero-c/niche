from services.playlist_maker.NicheTrackFinder import NicheTrackFinder
from services._shared_classes.PlaylistRequest import PlaylistRequest, Language, NicheLevel
from services._shared_classes.Playlist import Playlist
from services.playlist_maker.utils.artists_count_check import likely_under_count_playlist
from auth.SpotifyUser import SpotifyUser
import time

def do(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> str:
    t0     = time.time()
    user   = SpotifyUser()
    req    = PlaylistRequest(user, year_min, language, niche_level, sec_min, sec_max, genre)
    finder = NicheTrackFinder(req, user)
    songs  = finder.find_niche_tracks()
    pl     = Playlist(songs, req, user)
    t1     = time.time()
    total  = (t1-t0)/60
    print(f'TOTAL MINUTES RUN: {total}')

    print(pl.url)
    return (pl.url)

def playlist_likely_undersized(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> bool:
    user = SpotifyUser()
    return(likely_under_count_playlist(PlaylistRequest(user, year_min, language, niche_level, sec_min, sec_max, genre)))

if __name__ == '__main__':
    do(2000, Language.ANY, NicheLevel.ONLY_KINDA, 120, 360, 'latin')
