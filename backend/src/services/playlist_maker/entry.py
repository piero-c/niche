from services.playlist_maker.NicheTrackFinder import NicheTrackFinder
from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language, NicheLevel
from auth.SpotifyUser import SpotifyUser

def create(year_min: int, language: Language, niche_level: NicheLevel, sec_min: int, sec_max: int, genre: str) -> str:
    user   = SpotifyUser()
    req    = PlaylistRequest(user, year_min, language, niche_level, sec_min, sec_max, genre)
    finder = NicheTrackFinder(req, user)
    pl     = finder.create_playlist()

    print(pl.url)
    return (pl.url)

if __name__ == '__main__':
    create(2000, Language.ENGLISH, NicheLevel.MODERATELY, 120, 360, 'hip hop')