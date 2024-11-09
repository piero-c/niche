import random

from src.utils.spotify_util import NicheTrack, extract_id, SpotifyTrack, SpotifyArtist
from src.utils.logger       import logger
from src.utils.util         import sleep, LANGMAP, NICHEMAP, RequestType

from src.services._shared_classes.Validator       import Validator
from src.services._shared_classes.PlaylistRequest import PlaylistRequest
from src.services._shared_classes.Track           import Track
from src.services._shared_classes.Artist          import Artist
from src.services.profile.playlists               import get_playlist_tracks

from src.models.pydantic.Playlist import Playlist as PlaylistModel
from src.models.pydantic.Request  import Request  as RequestModel

from src.db.DAOs.RequestsDAO  import RequestDAO
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.db.DB                import DB

from src.auth.SpotifyUser import spotify_user



def _get_playlist_ids(playlist_url: str, type: str) -> list[str]:
    """Get track or artist ids from playlist

    Args:
        playlist_url (str): Url
        type (str): The type of ids to get. Must be one of 'track', 'artist'

    Returns:
        list[str]: The ids (spotify)
    """
    assert((type == 'track') or (type == 'artist'))
    # Get the ids of songs in the playlist to ensure we don't add a duplicate
    playlist_tracks: list[NicheTrack] = get_playlist_tracks(playlist_url)
    if (type == 'track'):
        ids_in_playlist = [extract_id(track.get('spotify_url'), 'track') for track in playlist_tracks]
    elif (type == 'artist'):
        ids_in_playlist = [track.get('artist_spotify_id', '') for track in playlist_tracks]
    
    return(ids_in_playlist)

def _get_playlist_request(playlist_url: str) -> PlaylistRequest:
    """Get the request associated with a playlist

    Args:
        playlist_url (str): Url

    Returns:
        PlaylistRequest: PlaylistRequest Instance
    """
    db = DB()
    pdao = PlaylistDAO(db)
    # Get the playlist entry by the link
    playlist: PlaylistModel = pdao.read_all({'link': playlist_url})[0] # Should be unique anyways
    rdao = RequestDAO(db)
    # Get the request from the playlist
    request: RequestModel = rdao.read_by_id(playlist.request)

    # Make a playlist request object from the request that generated the playlist at the request of the playlist generator. Don't add it to the db.
    playlist_request = PlaylistRequest(
        songs_min_year_created = request.params.songs_min_year_created,
        language               = LANGMAP.get(request.params.language),
        niche_level            = NICHEMAP.get(request.params.niche_level),
        songs_length_min_secs  = request.params.songs_length_min_secs,
        songs_length_max_secs  = request.params.songs_length_max_secs,
        genre                  = request.params.genre,
        add_to_db              = False
    )    
    return(playlist_request)

def artist_valid_for_insert(artist: SpotifyArtist, playlist_url: str) -> bool:
    """Check if an artist is valid to insert into a playlist

    Args:
        artist (SpotifyArtist): The artist as given by spotify
        playlist_url (str): Url

    Returns:
        bool: Is it?
    """
    artist_ids_in_playlist = _get_playlist_ids(playlist_url, 'artist')
    playlist_request = _get_playlist_request(playlist_url)

    validator = Validator(playlist_request)

    # TODO - language check will fail with no mbid :( find a way to look it up or get languages from spotify
    #     TODO then go to issue list and sort shit out
    artist_obj = Artist(artist.get('name', ''), 'no id')
    artist_obj.attach_spotify_artist(artist)
    # If not excluded and the artist isnt already in the playlist
    if (((artist_obj.spotify_artist_id) not in artist_ids_in_playlist) and (not validator.artist_excluded_reason_spotify(artist_obj)) and (not validator.artist_excluded_language(artist_obj, mb_check=False))):
        return(True)
    return(False)

def track_valid_for_insert(track: SpotifyTrack, playlist_url: str) -> bool:
    """Check if a track is valid to insert into a playlist

    Args:
        track (SpotifyTrack): The track as given by spotify
        playlist_url (str): Url

    Returns:
        bool: Is it!
    """
    song_ids_in_playlist = _get_playlist_ids(playlist_url, 'track')
    playlist_request = _get_playlist_request(playlist_url)

    validator = Validator(playlist_request)

    track_obj = Track(track.get('name'), "No Name")
    # No need to check artist id since we don't care who made it (assume the artist was already considered valid)
    track_obj.attach_spotify_track_information_from_spotify_track(track)
    if((track.get('id') not in song_ids_in_playlist) and (validator.validate_track(track_obj))):
        return(True)
    return(False)

def add_valid_track(track_uri: str, playlist_url: str) -> str | None:
    """Add pre-validated track

    Args:
        track_uri (str): _description_
        playlist_url (str): _description_

    Returns:
        str | None: _description_
    """
    playlist_id = extract_id(playlist_url, 'playlist')
    logger.info(f'Adding track with uri {track_uri}')
    
    ## BEGIN REQUEST ##
    # Get the spotify artist
    spotify_user.execute('playlist_add_items', playlist_id=playlist_id, items=[track_uri])
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##
    return(track_uri)


def validate_and_add_track(track: SpotifyTrack, playlist_url: str) -> str | None:
    """Validate the track for the playlist and add it

    Args:
        track (SpotifyTrack): Track
        playlist_url (str): Url

    Returns:
        str | None: Track uri if added
    """
    track_uri = track_valid_for_insert(track, playlist_url)

    if (track_uri):
        add_valid_track(track_uri, playlist_url)
    return(None)

def add_more_songs_for_artist(playlist_url: str, artist_spotify_id: str, num_songs: int) -> list[str]:
    """Add more songs by the specified artist to the playlist (must already be in the playlist)

    Args:
        playlist_url (str): Url
        artist_spotify_id (str): Artist spotify id
        num_songs (int): Number of songs by the artist to add

    Returns:
        list[str]: List of added track uris
    """
    assert(artist_spotify_id in _get_playlist_ids(playlist_url, 'artist'))
    logger.info(f'Adding tracks for artist id {artist_spotify_id}')
    
    ## BEGIN REQUEST ##
    # Get the spotify artist
    top_tracks = spotify_user.execute('artist_top_tracks', artist_spotify_id).get('tracks', [])
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##
    random.shuffle(top_tracks)

    uris_added = []
    # Add the specified number of songs by the artist
    for track in top_tracks:
        if (len(uris_added) >= num_songs):
            break
        added_uri = validate_and_add_track(track, playlist_url)
        if (added_uri):
            uris_added.append(added_uri)

    return(uris_added)

if __name__ == '__main__':
    print(add_more_songs_for_artist('https://open.spotify.com/playlist/2atGhoOdWEUKN4BjcGm7qn', '3jvWpZJpokYCoT0QV4OJg0', 1))





