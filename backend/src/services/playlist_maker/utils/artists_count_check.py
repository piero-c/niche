from numpy import mean

from src.db.DB               import DB
from src.db.DAOs.RequestsDAO import RequestDAO
from src.db.DAOs.ArtistsDAO  import ArtistsDAO

from src.models.pydantic.Request import Params

from src.services._shared_classes.PlaylistRequest import PlaylistRequest

from src.utils.util import LANGMAP, NICHEMAP, MIN_SONGS_FOR_PLAYLIST_GEN

def average_valid_artists_pct(request: PlaylistRequest) -> float:
    """From past requests, the average percentage of valid artists

    Args:
        request (PlaylistRequest): The request

    Returns:
        float: The average valid percent
    """
    db = DB()
    rdao = RequestDAO(db)
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
    pcts = [r.stats.percent_artists_valid for r in old_requests if r.stats.percent_artists_valid]

    if (not pcts):
        return(-1)

    return(mean(pcts))

def likely_under_count_playlist(request: PlaylistRequest, size: int = MIN_SONGS_FOR_PLAYLIST_GEN) -> bool:
    """Return true if the playlist for the request is likely to be under the requested size

    Args:
        request (PlaylistRequest): The request
        size (int, Optional): The size of the playlist. Defaults to 0 (request playlist length)

    Returns:
        bool: Will it likely be undersized
    """
    if (not size):
        size = request.playlist_min_length
    db = DB()

    adao = ArtistsDAO(db)

    # Get artists in the genre
    artists_count = adao.count_artists_in_genre(request.genre)

    avg = average_valid_artists_pct(request) / 100

    if (avg < 0):
        return(False)

    # Get the expected number of artists needed
    artists_needed = size / avg

    return(artists_count < artists_needed)

if __name__ == '__main__':
    print(likely_under_count_playlist(PlaylistRequest(2000, LANGMAP.get('English'), NICHEMAP.get('Moderately'), 120, 360, 'classic rock', False)))