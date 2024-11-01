from services.playlist_maker.NicheTrackFinder import NicheTrackFinder
from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language, NicheLevel
from auth.SpotifyUser import SpotifyUser
import time

def main():
    t0     = time.time()
    user   = SpotifyUser()
    req    = PlaylistRequest(2000, Language.ENGLISH, NicheLevel.MODERATELY, 120, 360, 'hip hop')
    finder = NicheTrackFinder(req, user)
    pl     = finder.create_playlist()
    t1     = time.time()
    total  = (t1-t0)/60
    print(f'TOTAL MINUTES RUN: {total}')

    print(pl.url)
if __name__ == '__main__':
    main()
