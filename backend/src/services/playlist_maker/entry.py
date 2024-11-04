from services.playlist_maker.NicheTrackFinder import NicheTrackFinder
from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language, NicheLevel
from services.playlist_maker.Playlist import Playlist
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

if __name__ == '__main__':
    do(2000, Language.ANY, NicheLevel.MODERATELY, 120, 360, 'k-pop')