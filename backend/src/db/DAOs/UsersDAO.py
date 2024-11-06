from typing import Optional, List
from pymongo.results import UpdateResult, DeleteResult
from bson import ObjectId
from src.models.pydantic.User import User
from src.db.DB import DB
from src.db.DAOs.baseDAO import BaseDAO
from src.models.pydantic.BaseSchema import clean_update_data
from src.db.util import OperationResult

class UserDAO(BaseDAO[User]):
    """
    Data Access Object for User collection.
    """

    def __init__(self, db: DB) -> None:
        super().__init__(db.get_collection("users"), User)

    def create_or_update_by_spotify_id(self, user: User) -> OperationResult:
        """
        Creates a new user or updates an existing user based on Spotify ID.

        Args:
            user (User): The user data to insert or update.

        Returns:
            OperationResult: A result object that contains the operation result and the document's ObjectId.
        """
        existing_user = self.collection.find_one({"spotify_id": user.spotify_id})
        user_clean = clean_update_data(user.model_dump(by_alias=True))

        if (existing_user):
            # Update existing user and retrieve ObjectId from the existing document
            update_result = self.collection.update_one(
                {"spotify_id": user.spotify_id},
                {"$set": user_clean}
            )
            object_id = existing_user["_id"]  # Get _id from the existing document
            return (OperationResult(update_result, object_id))
        else:
            # Insert as a new user
            insert_result = self.collection.insert_one(user_clean)
            return (OperationResult(insert_result, insert_result.inserted_id))

    def read_all(self, filter: dict = {}) -> List[User]:
        """
        Reads all users matching a filter.

        Args:
            filter (dict): The filter criteria for finding users.

        Returns:
            List[User]: A list of matching users.
        """
        documents = self.collection.find(filter)
        return ([User.model_validate(doc) for doc in documents])

    def read_by_spotify_id(self, spotify_id: str) -> Optional[User]:
        """
        Reads a user by their Spotify ID.

        Args:
            spotify_id (str): The Spotify ID of the user to find.

        Returns:
            Optional[User]: The found user, or None if not found.
        """
        raw_data = self.collection.find_one({"spotify_id": spotify_id})
        return (User.model_validate(raw_data) if (raw_data) else None)

    def update_display_name(self, user_id: str, display_name: str) -> UpdateResult:
        """
        Updates the display name of a user by their ObjectId.

        Args:
            user_id (str): The ObjectId of the user to update.
            display_name (str): The new display name for the user.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"display_name": display_name}}))

    def delete_by_spotify_id(self, spotify_id: str) -> DeleteResult:
        """
        Deletes a user document by their Spotify ID.

        Args:
            spotify_id (str): The Spotify ID of the user to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"spotify_id": spotify_id}))
