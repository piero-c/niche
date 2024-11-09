import random

from src.utils.spotify_util import NicheTrack, SPOTIFY_MAX_LIMIT_RECS, SpotifyTrack, SpotifyArtist, SpotifyArtistID
from src.utils.util         import convert_s_to_ms, MIN_SONGS_FOR_PLAYLIST_GEN
from src.utils.logger       import logger

from src.models.pydantic.Playlist import Playlist as PlaylistModel
from src.models.pydantic.Request  import Request as RequestModel

from src.db.DAOs.RequestsDAO  import RequestDAO
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.db.DB                import DB

from src.services.profile.playlists               import get_playlist_tracks
from src.services.playlist_editor.add_songs       import artist_valid_for_insert, track_valid_for_insert
from src.services.genre_handling.valid_genres     import genre_is_spotify
from src.services._shared_classes.PlaylistRequest import PlaylistRequest

from src.auth.SpotifyUser import spotify_user

from config.personal_init import token

def _get_random_artist_ids(tracks: list[NicheTrack], num: int = 4) -> list[SpotifyArtistID]:
    """Get num random artist spotify ids from the tracks

    Args:
        tracks (NicheTrack): Pool of tracks to choose artist ids from
        num (int, optional): Number of ids to get. Defaults to 4.

    Returns:
        list[SpotifyArtistID]: List of spotify ids
    """
    tracks_copy = tracks.copy()
    seed_ids = list(set([track.get('artist_spotify_id', '') for track in tracks_copy]))
    return(random.sample(seed_ids, num) if len(seed_ids) > num else seed_ids)

# TODO - some kind of likeness metric
def get_recommendations(playlist_url: str, num: int = 1) -> list[SpotifyTrack]:
    """Get num recommendations for the playlist from spotify

    Args:
        playlist_url (str): Url
        num (int, optional): Number of recs to get. Defaults to 1.
        delete_after(bool, optional): Delete the playlist after? Defaults to False.

    Returns:
        list[SpotifyTrack]: The recs
    """
    artist_seeds_num = MIN_SONGS_FOR_PLAYLIST_GEN - 1
    recommended_tracks = []
    added_artist_ids = []
    added_track_ids = []

    db = DB()
    pdao = PlaylistDAO(db)
    # Get the playlist entry by the link
    playlist: PlaylistModel = pdao.read_all({'link': playlist_url})[0] # Should be unique anyways
    rdao = RequestDAO(db)
    # Get the request from the playlist
    request: RequestModel = rdao.read_by_id(playlist.request)

    playlist_tracks = get_playlist_tracks(playlist_url)
    playlist_request = PlaylistRequest.from_model(request_model=request, add_to_db=False)

    if (genre_is_spotify(request.params.genre)):
        seed_artists = _get_random_artist_ids(playlist_tracks, artist_seeds_num)
        seed_genres = [request.params.genre]
    else:
        seed_artists = _get_random_artist_ids(playlist_tracks, artist_seeds_num + 1)
        seed_genres = []

    # Get the max number of recs, shuffle them, add the first num valid ones

    logger.info(f'Getting recommendations for playlist {playlist_url}...')

    if (seed_genres):
        recs = spotify_user.execute(
            'recommendations',
            seed_artists    = seed_artists,
            seed_genres     = seed_genres,
            limit           = SPOTIFY_MAX_LIMIT_RECS,
            min_duration_ms = convert_s_to_ms(request.params.songs_length_min_secs),
            max_duration_ms = convert_s_to_ms(request.params.songs_length_max_secs),
        )
    else:
        recs = spotify_user.execute(
            'recommendations',
            seed_artists    = seed_artists,
            limit           = SPOTIFY_MAX_LIMIT_RECS,
            min_duration_ms = convert_s_to_ms(request.params.songs_length_min_secs),
            max_duration_ms = convert_s_to_ms(request.params.songs_length_max_secs),
        )

    logger.info(f'Recieved {len(recs.get('tracks'))} recommendations')

    rec_tracks = recs.get('tracks', '')
    random.shuffle(rec_tracks)

    for track in rec_tracks:
        if (len(recommended_tracks) >= num):
            break
        logger.info(f'Checking validity for track {track.get('name', '')}')
        track_artist_id = track.get('artists', [{}])[0].get('id', '')
        track_artist: SpotifyArtist = spotify_user.execute('artist', track_artist_id)

        if (not track_artist):
            continue
        # TODO - try to make validity check for additional songs into an object so we dont have to query and shit (give requests cache to validator and cache artist ids?)

        elif (artist_valid_for_insert(track_artist, playlist_tracks, playlist_request, added_artist_ids) and track_valid_for_insert(track, playlist_tracks, playlist_request, added_track_ids)):
            recommended_tracks.append(track)
            added_artist_ids.append(track_artist_id)
            added_track_ids.append(track.get('id', ''))
    
    return(recommended_tracks)

if __name__ == '__main__':
    spotify_user.initialize(token)
    print(get_recommendations('https://open.spotify.com/playlist/46r84vZRBBY0NkzA8x06Tr', 1))