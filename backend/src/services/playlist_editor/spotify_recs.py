from src.utils.spotify_util import SpotifyTrack, SPOTIFY_MAX_LIMIT_RECS, SPOTIFY_MAX_SEEDS_RECS, SpotifyArtist
from src.models.pydantic.Playlist import Playlist as PlaylistModel
from src.models.pydantic.Request import Request as RequestModel
from src.db.DAOs.RequestsDAO import RequestDAO
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.db.DB import DB
from src.auth.SpotifyUser import SpotifyUser
from src.utils.util import sleep, RequestType, convert_s_to_ms
from src.services.profile.playlists import get_playlist_tracks, PlaylistTracks
from src.services.playlist_editor.add_songs import artist_valid_for_insert, track_valid_for_insert, add_valid_track

import random

def _get_random_artist_ids(tracks: PlaylistTracks, num: int = 4) -> list[str]:
    """_summary_

    Args:
        tracks (PlaylistTracks): _description_
        num (int, optional): _description_. Defaults to 4.

    Returns:
        list[str]: _description_
    """
    tracks_copy = tracks.copy()
    seed_ids = list(set([track.get('artists', [{}])[0].get('artist_id', '') for track in tracks_copy]))
    return(random.sample(seed_ids, num) if len(seed_ids) > num else seed_ids)


def get_recommendations(playlist_url: str, user: SpotifyUser, num: int = 1) -> list[SpotifyTrack]:
    """_summary_

    Args:
        playlist_url (str): _description_
        user (SpotifyUser): _description_
        num (int, optional): _description_. Defaults to 1.

    Returns:
        list[SpotifyTrack]: _description_
    """
    assert(num > 0 and num <= 10)
    artist_seeds_num = SPOTIFY_MAX_SEEDS_RECS - 1
    reccomended_tracks = []

    db = DB()
    pdao = PlaylistDAO(db)
    # Get the playlist entry by the link
    playlist: PlaylistModel = pdao.read_all({'link': playlist_url})[0] # Should be unique anyways
    rdao = RequestDAO(db)
    # Get the request from the playlist
    request: RequestModel = rdao.read_by_id(playlist.request)

    playlist_tracks = get_playlist_tracks(playlist_url, user)
    seed_artists = _get_random_artist_ids(playlist_tracks, artist_seeds_num)

    seed_genres = [request.params.genre]

    # Get 100, shuffle, get one, validate artist and track, ensure no otehr validations are needed by add track (no throw), return track

    ## BEGIN REQUEST ##
    recs = user.execute(
        'recommendations',
        seed_artists=seed_artists,
        seed_genres=seed_genres,
        limit=SPOTIFY_MAX_LIMIT_RECS,
        min_duration_ms=convert_s_to_ms(request.params.songs_length_min_secs),
        max_duration_ms=convert_s_to_ms(request.params.songs_length_max_secs),
    )
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##

    rec_tracks = recs.get('tracks', '')
    random.shuffle(rec_tracks)

    for track in rec_tracks:
        track_artist_id = track.get('artists', [{}])[0].get('id', '')
        ## BEGIN REQUEST ##
        track_artist: SpotifyArtist = user.execute('artist', track_artist_id)
        sleep(RequestType.SPOTIFY)
        ## END REQUEST ##
        if (artist_valid_for_insert(track_artist, playlist_url, user) and track_valid_for_insert(track, playlist_url, user)):
            reccomended_tracks.append(track)
        if (len(reccomended_tracks) >= num):
            break
    
    return(reccomended_tracks)

if __name__ == '__main__':
    print(add_valid_track(get_recommendations('https://open.spotify.com/playlist/1w4iuLNHMAzGxI6ZOl6m5n', SpotifyUser(), 1)[0].get('uri'), 'https://open.spotify.com/playlist/1w4iuLNHMAzGxI6ZOl6m5n', SpotifyUser()))