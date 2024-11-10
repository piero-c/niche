from src.auth.SpotifyUser import spotify_user
from src.utils.spotify_util import extract_id
from src.utils.logger import logger

from config.personal_init import token

# TODO - for this and add valid update stats of request? nah
def remove_song(track_uri: str, playlist_url: str):
    """_summary_

    Args:
        track_uri (str): _description_
        playlist_url (str): _description_
    """
    playlist_id = extract_id(playlist_url, 'playlist')

    logger.info(f'Removing track with uri {track_uri}')

    # Get the spotify artist
    spotify_user.execute('playlist_remove_all_occurrences_of_items', playlist_id=playlist_id, items=[track_uri])
    return(track_uri)

if __name__ == '__main__':
    spotify_user.initialize(token)
    remove_song('spotify:track:2xcPOFUsTdRqnZUop0VrCh', 'https://open.spotify.com/playlist/64p41LoV9nvGisH7mWf26a')