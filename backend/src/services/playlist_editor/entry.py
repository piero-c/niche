from services.playlist_editor.add_songs import add_more_songs_for_artist
from services.playlist_editor.spotify_recs import get_recommendations
from auth.SpotifyUser import SpotifyUser
from utils.spotify_util import SpotifyTrack
def add_songs_by_artist(playlist_url: str, artist_id: str, user: SpotifyUser, num_songs: int) -> list[str]:
    """_summary_

    Args:
        playlist_url (str): _description_
        artist_id (str): _description_
        user (SpotifyUser): _description_
        num_songs (int): _description_

    Returns:
        list[str]: _description_
    """
    return(add_more_songs_for_artist(playlist_url, artist_id, user, num_songs))

def get_valid_track_recommendations(playlist_url: str, user: SpotifyUser, num_tracks: int = 1) -> list[SpotifyTrack]:
    """_summary_

    Args:
        playlist_url (str): _description_
        user (SpotifyUser): _description_
        num_tracks (int, optional): _description_. Defaults to 1.

    Returns:
        list[SpotifyTrack]: _description_
    """
    return(get_recommendations(playlist_url, user, num_tracks))