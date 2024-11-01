from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
from models.pydantic.RequestsCache import RequestsCache, Excluded
from db.DB import DB

class RequestsCacheDAO:
    """
    Data Access Object for RequestsCache collection.

    Provides methods to create, read, update, and delete RequestsCache data in MongoDB.
    """

    def __init__(self, db: DB) -> None:
        """
        Initializes the RequestsCacheDAO with a database instance.

        Args:
            db (DB): The database instance.
        """
        self.collection: Collection = db.get_collection("requests_cache")

    def create(self, requests_cache: RequestsCache) -> InsertOneResult:
        """
        Inserts a new requests_cache document into the collection.

        Args:
            requests_cache (RequestsCache): The RequestsCache data to insert.

        Returns:
            InsertOneResult: The result of the insertion operation.
        """
        return (self.collection.insert_one(requests_cache.model_dump(by_alias=True)))

    def read_by_id(self, cache_id: str) -> Optional[RequestsCache]:
        """
        Reads a RequestsCache entry by its ObjectId.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to find.

        Returns:
            Optional[RequestsCache]: The found RequestsCache entry, or None if not found.
        """
        raw_data = self.collection.find_one({"_id": ObjectId(cache_id)})
        return (RequestsCache.model_validate(raw_data) if (raw_data) else None)

    def read_all(self, filter: dict = {}) -> List[RequestsCache]:
        """
        Reads all RequestsCache entries matching a filter.

        Args:
            filter (dict): The filter criteria for finding RequestsCache entries.

        Returns:
            List[RequestsCache]: A list of matching RequestsCache entries.
        """
        documents = self.collection.find(filter)
        return ([RequestsCache.model_validate(doc) for doc in documents])

    def update(self, cache_id: str, update_data: dict) -> UpdateResult:
        """
        Updates a RequestsCache document by its ObjectId.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to update.
            update_data (dict): The data to update in the RequestsCache document.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one({"_id": ObjectId(cache_id)}, {"$set": update_data}))

    def delete(self, cache_id: str) -> DeleteResult:
        """
        Deletes a RequestsCache document by its ObjectId.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"_id": ObjectId(cache_id)}))

    def read_by_params(self, params: Dict[str, Any]) -> List[RequestsCache]:
        """
        Reads RequestsCache entries based on specific parameters within the `params` field.

        Args:
            params (Dict[str, Any]): The parameters to match in the `params` field of the RequestsCache entries.

        Returns:
            List[RequestsCache]: A list of RequestsCache entries that match the given parameters.
        """
        query = {f"params.{key}": value for key, value in params.items()}
        documents = self.collection.find(query)
        return ([RequestsCache.model_validate(doc) for doc in documents])

    def add_excluded_entry(self, cache_id: str, excluded: Excluded) -> UpdateResult:
        """
        Adds an `Excluded` entry to the `excluded` list in a RequestsCache document.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to update.
            excluded (Excluded): The Excluded entry to add.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one(
            {"_id": ObjectId(cache_id)},
            {"$push": {"excluded": excluded.model_dump(by_alias=True)}}
        ))

    def delete_excluded_entry(self, cache_id: str, mbid: str) -> UpdateResult:
        """
        Deletes an `Excluded` entry from the `excluded` list based on mbid in a RequestsCache document.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to update.
            mbid (str): The mbid of the Excluded entry to delete.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one(
            {"_id": ObjectId(cache_id)},
            {"$pull": {"excluded": {"mbid": mbid}}}
        ))

    def read_excluded_by_reason(self, cache_id: str, reason: str) -> List[Excluded]:
        """
        Reads the `Excluded` entries for a specific RequestsCache entry that were excluded for a certain reason.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to search.
            reason (str): The exclusion reason to filter by within the `excluded` list.

        Returns:
            List[Excluded]: A list of `Excluded` entries matching the specified reason in the specified RequestsCache entry.
        """
        # Find the specific RequestsCache entry
        raw_data = self.collection.find_one(
            {"_id": ObjectId(cache_id)},
            {"excluded": {"$elemMatch": {"reason_excluded": reason}}}
        )

        # If entry exists and has excluded items, validate and return them; otherwise, return an empty list
        excluded_entries = raw_data.get("excluded", []) if raw_data else []
        return ([Excluded.model_validate(entry) for entry in excluded_entries])
