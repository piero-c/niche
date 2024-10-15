from scripts.playlist_maker.NicheTrackFinder import NicheTrackFinder
from scripts.playlist_maker.Playlist import Playlist
from scripts.playlist_maker.PlaylistRequest import PlaylistRequest, Language, PlaylistLength, NicheLevel

def main():
    req = PlaylistRequest(2000, Language.ANY, PlaylistLength.SHORT, NicheLevel.VERY, 120, 360, 2, 'indie pop')
    finder = NicheTrackFinder(req)
    pl = finder.create_playlist()

    print(pl.url)
if __name__ == '__main__':
    main()
