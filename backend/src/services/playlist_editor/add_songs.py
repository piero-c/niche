from utils.spotify_util import extract_id, SpotifyTrack
from services._shared_classes.Validator import Validator
from services._shared_classes.PlaylistRequest import PlaylistRequest
from services._shared_classes.Track import Track
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

# TODO - take api hits out here make interface fns w spotify user
    # TODO - Work on adding spotify recs (get recs, validate artist, add track) (in other file)


def add_track(track: SpotifyTrack, playlist_url: str, ids_to_not_add: list[str], user: SpotifyUser):
    db = DB()
    pdao = PlaylistDAO(db)
    # Get the playlist entry by the link
    playlist: PlaylistModel = pdao.read_all({'link': playlist_url})[0] # Should be unique anyways
    rdao = RequestDAO(db)
    # Get the request from the playlist
    request: RequestModel = rdao.read_by_id(playlist.request)
    playlist_id = extract_id(playlist_url, 'playlist')
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

    validator = Validator(playlist_request, user)

    track_obj = Track(track.get('name'), "No Name", user)
    # No need to check artist id since we don't care who made it (assume the artist was already considered valid)
    track_obj.attach_spotify_track_information_from_spotify_track(track)
    if ((track.get('id') not in ids_to_not_add) and (validator.validate_track(track_obj))):
        ## BEGIN REQUEST ##
        # Get the spotify artist
        user.client.playlist_add_items(playlist_id=playlist_id, items=[track_obj.spotify_uri])
        sleep(RequestType.SPOTIFY)
        ## END REQUEST ##
        return(track_obj.spotify_uri)


def add_more_songs_for_artist(playlist_url: str, artist_id: str, user: SpotifyUser, num_songs: int) -> list[str]:
    ## BEGIN REQUEST ##
    # Get the spotify artist
    artist = user.client.artist(artist_id)
    sleep(RequestType.SPOTIFY)
    ## END REQUEST ##

    # Get the ids of songs by this artist in the playlist already
    playlist_tracks = get_playlist_tracks(playlist_url, user)
    existing_tracks_by_artist = list(filter(lambda track: artist.get('id') in [track_artist.get('artist_id', "") for track_artist in track.get('artists', [])], playlist_tracks))
    existing_song_ids_by_artist = [extract_id(track.get('spotify_track_url'), 'track') for track in existing_tracks_by_artist]
    
    logger.info(existing_song_ids_by_artist)

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
        added_uri = add_track(track, playlist_url, existing_song_ids_by_artist, user)
        if (added_uri):
            uris_added.append(added_uri)

    return(uris_added)

if __name__ == '__main__':
    print(add_more_songs_for_artist('https://open.spotify.com/playlist/2atGhoOdWEUKN4BjcGm7qn', '3jvWpZJpokYCoT0QV4OJg0', SpotifyUser(), 1))





