from src.services.playlist_maker.NicheTrackFinder import NicheTrackFinder
from src.services._shared_classes.PlaylistRequest import PlaylistRequest, Language, NicheLevel
from src.services._shared_classes.Playlist import Playlist
from src.services.playlist_maker.utils.artists_count_check import likely_under_count_playlist
import time

from config.personal_init import token
from src.auth.SpotifyUser import spotify_user

def do(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> str:
    t0     = time.time()
    req    = PlaylistRequest(year_min, language, niche_level, sec_min, sec_max, genre)
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
    return(likely_under_count_playlist(PlaylistRequest(year_min, language, niche_level, sec_min, sec_max, genre)))

if __name__ == '__main__':
    spotify_user.initialize(token)
    do(2000, Language.ANY, NicheLevel.ONLY_KINDA, 120, 360, 'mpb')
