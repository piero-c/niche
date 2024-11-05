from utils.spotify_util import extract_id, SpotifyTrack, SpotifyArtist
from services._shared_classes.Validator import Validator
from services._shared_classes.PlaylistRequest import PlaylistRequest
from services._shared_classes.Track import Track
from services._shared_classes.Artist import Artist
from models.pydantic.Playlist import Playlist as PlaylistModel
from models.pydantic.Request import Request as RequestModel
from db.DAOs.RequestsDAO import RequestDAO
from db.DAOs.PlaylistsDAO import PlaylistDAO
from db.DB import DB
from auth.SpotifyUser import SpotifyUser
from utils.util import LANGMAP, NICHEMAP, sleep, RequestType
from services.profile.playlists import get_playlist_tracks
from utils.logger import logger

import random

# TODO - take api hits out here make interface fns w spotify user (maybe for client methods sleep for not interfaced ones)
    # TODO - Work on adding spotify recs (get recs, validate artist, add track) (in other file)
# TODO - Add logging here

# TODO - take validation part out or wait just validate in the spotify thing and make sure this won't fail

def _get_playlist_song_ids(playlist_url: str, user: SpotifyUser) -> list[str]:
    # Get the ids of songs in the playlist to ensure we don't add a duplicate
    playlist_tracks = get_playlist_tracks(playlist_url, user)
    song_ids_in_playlist = [extract_id(track.get('spotify_track_url'), 'track') for track in playlist_tracks]
    return(song_ids_in_playlist)

def _get_playlist_request(playlist_url: str, user: SpotifyUser) -> PlaylistRequest:
    db = DB()
    pdao = PlaylistDAO(db)
    # Get the playlist entry by the link
    playlist: PlaylistModel = pdao.read_all({'link': playlist_url})[0] # Should be unique anyways
    rdao = RequestDAO(db)
    # Get the request from the playlist
    request: RequestModel = rdao.read_by_id(playlist.request)
    # Make a playlist request object from the request that generated the playlist
    playlist_request = PlaylistRequest(
        user=user,
        songs_min_year_created=request.params.songs_min_year_created,
        language=LANGMAP.get(request.params.language),
        niche_level=NICHEMAP.get(request.params.niche_level),
        songs_length_min_secs=request.params.songs_length_min_secs,
        songs_length_max_secs=request.params.songs_length_max_secs,
        genre=request.params.genre
    )    
    return(playlist_request)

def _validate_track_for_insert(track: SpotifyTrack, user: SpotifyUser, request: PlaylistRequest, song_ids_in_playlist: list[str]) -> str | None:
    validator = Validator(request, user)

    track_obj = Track(track.get('name'), "No Name", user)
    # No need to check artist id since we don't care who made it (assume the artist was already considered valid)
    track_obj.attach_spotify_track_information_from_spotify_track(track)
    if(track.get('id') not in song_ids_in_playlist) and (validator.validate_track(track_obj)):
        return(track_obj.spotify_uri)
    return(None)

def artist_valid_for_insert(artist: SpotifyArtist, playlist_url: str, user: SpotifyUser) -> bool:
    playlist_request = _get_playlist_request(playlist_url, user)
    validator = Validator(playlist_request, user)

    artist_obj = Artist(artist.get('name', ''), 'no id', user)
    artist_obj.attach_spotify_artist(artist)
    if (validator.artist_excluded_reason_spotify(artist_obj)):
        return(False)
    return(True)

def track_valid_for_insert(track: SpotifyTrack, playlist_url: str, user: SpotifyUser) -> str | None:
    song_ids_in_playlist = _get_playlist_song_ids(playlist_url, user)
    playlist_request = _get_playlist_request(playlist_url, user)
    logger.info(f'IDS IN PLAYLIST: {song_ids_in_playlist}')

    track_uri = _validate_track_for_insert(track, user, playlist_request, song_ids_in_playlist)
    return(track_uri)

def validate_and_add_track(track: SpotifyTrack, playlist_url: str, user: SpotifyUser) -> str | None:
    playlist_id = extract_id(playlist_url, 'playlist')
    track_uri = track_valid_for_insert(track, playlist_url, user)

    if (track_uri):
        ## BEGIN REQUEST ##
        # Get the spotify artist
        user.client.playlist_add_items(playlist_id=playlist_id, items=[track_uri])
        sleep(RequestType.SPOTIFY)
        ## END REQUEST ##
        return(track_uri)
    return(None)

def add_valid_track(track_uri: str, playlist_url: str, user: SpotifyUser) -> str | None:
    playlist_id = extract_id(playlist_url, 'playlist')
    ## BEGIN REQUEST ##
    # Get the spotify artist
    user.client.playlist_add_items(playlist_id=playlist_id, items=[track_uri])
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##
    return(track_uri)

def add_more_songs_for_artist(playlist_url: str, artist_id: str, user: SpotifyUser, num_songs: int) -> list[str]:
    ## BEGIN REQUEST ##
    # Get the spotify artist
    top_tracks = user.client.artist_top_tracks(artist_id).get('tracks', [])
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##

    random.shuffle(top_tracks)

    uris_added = []
    for track in top_tracks:
        if (len(uris_added) >= num_songs):
            break
        added_uri = validate_and_add_track(track, playlist_url, user)
        if (added_uri):
            uris_added.append(added_uri)

    return(uris_added)

if __name__ == '__main__':
    print(add_more_songs_for_artist('https://open.spotify.com/playlist/2atGhoOdWEUKN4BjcGm7qn', '3jvWpZJpokYCoT0QV4OJg0', SpotifyUser(), 1))





