from typing import List
from bson import ObjectId
from src.models.pydantic.Playlist import Playlist
from src.db.DB import DB
from src.db.DAOs.baseDAO import BaseDAO

class PlaylistDAO(BaseDAO[Playlist]):
    """
    Data Access Object for Playlist collection.
    """
    def __init__(self, db: DB) -> None:
        super().__init__(db.get_collection("playlists"), Playlist)

    def read_all(self, filter: dict = {}) -> List[Playlist]:
        """
        Reads all playlists matching a filter.

        Args:
            filter (dict): The filter criteria for finding playlists.

        Returns:
            List[Playlist]: A list of matching playlists.
        """
        documents = self.collection.find(filter)
        return ([Playlist.model_validate(doc) for doc in documents])

    def read_by_user(self, user_id: str) -> List[Playlist]:
        """
        Reads all playlists associated with a specific user.

        Args:
            user_id (str): The ObjectId of the user whose playlists are to be found.

        Returns:
            List[Playlist]: A list of playlists belonging to the specified user.
        """
        documents = self.collection.find({"user": ObjectId(user_id)})
        return ([Playlist.model_validate(doc) for doc in documents])
