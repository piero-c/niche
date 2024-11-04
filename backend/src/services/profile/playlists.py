from db.DB import DB
from db.DAOs.PlaylistsDAO import PlaylistDAO
from auth.SpotifyUser import SpotifyUser
from models.pydantic.Playlist import Playlist

def get_generated_playlists(user: SpotifyUser) -> list[Playlist]:
    """Get all playlists a user has generated

    Args:
        user (SpotifyUser): The user

    Returns:
        list[Playlist]: The playlists
    """
    return(PlaylistDAO(DB()).read_by_user(user_id=user.oid))

if __name__ == '__main__':
    print(len(get_generated_playlists(SpotifyUser())))