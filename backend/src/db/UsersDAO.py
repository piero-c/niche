from typing import Optional, List
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
from models.pydantic.User import User
from db.DB import DB

class UserDAO:
    """
    Data Access Object for User collection.

    Provides methods to create, read, update, and delete User data in MongoDB.
    """

    def __init__(self, db: DB) -> None:
        """
        Initializes the UserDAO with a database instance.

        Args:
            db (DB): The database instance.
        """
        self.collection: Collection = db.get_collection("users")

    def create(self, user: User) -> InsertOneResult:
        """
        Inserts a new user document into the collection.

        Args:
            user (User): The user data to insert.

        Returns:
            InsertOneResult: The result of the insertion operation.
        """
        return (self.collection.insert_one(user.model_dump(by_alias=True)))

    def read_by_id(self, user_id: str) -> Optional[User]:
        """
        Reads a user by its ObjectId.

        Args:
            user_id (str): The ObjectId of the user to find.

        Returns:
            Optional[User]: The found user, or None if not found.
        """
        raw_data = self.collection.find_one({"_id": ObjectId(user_id)})
        return (User.model_validate(raw_data) if (raw_data) else None)

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

    def update(self, user_id: str, update_data: dict) -> UpdateResult:
        """
        Updates a user document by its ObjectId.

        Args:
            user_id (str): The ObjectId of the user to update.
            update_data (dict): The data to update in the user document.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data}))

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

    def delete(self, user_id: str) -> DeleteResult:
        """
        Deletes a user document by its ObjectId.

        Args:
            user_id (str): The ObjectId of the user to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"_id": ObjectId(user_id)}))

    def delete_by_spotify_id(self, spotify_id: str) -> DeleteResult:
        """
        Deletes a user document by their Spotify ID.

        Args:
            spotify_id (str): The Spotify ID of the user to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"spotify_id": spotify_id}))
