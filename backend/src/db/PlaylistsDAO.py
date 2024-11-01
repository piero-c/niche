from typing import Optional, List
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
from models.pydantic.Playlist import Playlist
from db.DB import DB

class PlaylistDAO:
    """
    Data Access Object for Playlist collection.

    Provides methods to create, read, update, and delete Playlist data in MongoDB.
    """

    def __init__(self, db: DB) -> None:
        """
        Initializes the PlaylistDAO with a database instance.

        Args:
            db (DB): The database instance.
        """
        self.collection: Collection = db.get_collection("playlists")

    def create(self, playlist: Playlist) -> InsertOneResult:
        """
        Inserts a new playlist document into the collection.

        Args:
            playlist (Playlist): The playlist data to insert.

        Returns:
            InsertOneResult: The result of the insertion operation.
        """
        return (self.collection.insert_one(playlist.model_dump(by_alias=True)))

    def read_by_id(self, playlist_id: str) -> Optional[Playlist]:
        """
        Reads a playlist by its ObjectId.

        Args:
            playlist_id (str): The ObjectId of the playlist to find.

        Returns:
            Optional[Playlist]: The found playlist, or None if not found.
        """
        raw_data = self.collection.find_one({"_id": ObjectId(playlist_id)})
        return (Playlist.model_validate(raw_data) if (raw_data) else None)

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

    def update(self, playlist_id: str, update_data: dict) -> UpdateResult:
        """
        Updates a playlist document by its ObjectId.

        Args:
            playlist_id (str): The ObjectId of the playlist to update.
            update_data (dict): The data to update in the playlist document.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one({"_id": ObjectId(playlist_id)}, {"$set": update_data}))

    def delete(self, playlist_id: str) -> DeleteResult:
        """
        Deletes a playlist document by its ObjectId.

        Args:
            playlist_id (str): The ObjectId of the playlist to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"_id": ObjectId(playlist_id)}))
