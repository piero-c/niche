from db.DB import DB
from db.DAOs.RequestsDAO import RequestDAO
from db.DAOs.ArtistsDAO import ArtistsDAO
from models.pydantic.Request import Params
from services.playlist_maker.PlaylistRequest import PlaylistRequest
from utils.util import LANGMAP, NICHEMAP
from numpy import mean

from auth.SpotifyUser import SpotifyUser

def likely_under_count_playlist(request: PlaylistRequest) -> bool:
    """Return true if the playlist for the request is likely to be under the requested size

    Args:
        request (PlaylistRequest): The request

    Returns:
        bool: Will it likely be undersized
    """
    db = DB()

    rdao = RequestDAO(db)
    adao = ArtistsDAO(db)

    # Get artists in the genre
    artists_count = adao.count_artists_in_genre(request.genre)
    # Get all previous requests that match this one
    old_requests = rdao.read_by_params(
        Params(
            language=LANGMAP.inv.get(request.language),
            genre=request.genre,
            niche_level=NICHEMAP.inv.get(request.niche_level),
            songs_min_year_created=request.songs_min_year_created,
            songs_length_min_secs=request.songs_length_min_secs,
            songs_length_max_secs=request.songs_length_max_secs
        )
    )

    # Get all requests that have a percent_artists_valid field
    pcts = [r.stats.percent_artists_valid / 100 for r in old_requests if r.stats.percent_artists_valid]

    if (not pcts):
        return(False)

    avg = mean(pcts)

    if (avg <= 0):
        return(True)

    # Get the expected number of artists needed
    artists_needed = request.playlist_length / avg

    # Give 11% optimism error (if its likely to generate like 18 we'll be fine)
    artists_needed -= (artists_needed / 11)

    return(artists_count < artists_needed)

if __name__ == '__main__':
    print(likely_under_count_playlist(PlaylistRequest(SpotifyUser(), 2000, LANGMAP.get('English'), NICHEMAP.get('Moderately'), 120, 360, 'classic rock')))