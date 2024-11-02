from typing import List, Union
from pymongo.results import InsertOneResult, UpdateResult
from bson import ObjectId
from models.pydantic.RequestsCache import RequestsCache, Excluded, ParamsCache
from db.DB import DB
from db.DAOs.baseDAO import BaseDAO

# TODO - better way to clean update data then what currently doing (like to not update immutable fields)

class RequestsCacheDAO(BaseDAO[RequestsCache]):
    """
    Data Access Object for RequestsCache collection.
    """

    def __init__(self, db: DB) -> None:
        super().__init__(db.get_collection("requests_cache"), RequestsCache)

    def create_if_not_exists(self, params: ParamsCache) -> Union[RequestsCache, InsertOneResult]:
        """
        Creates a new RequestsCache entry if one does not exist with the given ParamsCache parameters.

        Args:
            params (ParamsCache): The parameters to check or create in the `params` field.

        Returns:
            Union[RequestsCache, InsertOneResult]: The existing or newly created RequestsCache entry.
        """
        params_dict = params.model_dump(by_alias=True)
        query = {f"params.{key}": value for key, value in params_dict.items()}
        
        existing_entry = self.collection.find_one(query)
        
        if (existing_entry):
            return (RequestsCache.model_validate(existing_entry))
        else:
            new_cache = RequestsCache(params=params, excluded=[])
            result = self.collection.insert_one(new_cache.model_dump(by_alias=True))
            return (result)

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

    def read_by_params(self, params: ParamsCache) -> List[RequestsCache]:
        """
        Reads RequestsCache entries based on specific parameters within the `params` field.

        Args:
            params (ParamsCache): The parameters to match in the `params` field of the RequestsCache entries.

        Returns:
            List[RequestsCache]: A list of matching RequestsCache entries.
        """
        params_dict = params.model_dump(by_alias=True)
        query = {f"params.{key}": value for key, value in params_dict.items()}
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
        raw_data = self.collection.find_one(
            {"_id": ObjectId(cache_id)},
            {"excluded": {"$elemMatch": {"reason_excluded": reason}}}
        )
        excluded_entries = raw_data.get("excluded", []) if raw_data else []
        return ([Excluded.model_validate(entry) for entry in excluded_entries])

    def check_and_update_or_add_excluded(self, cache_id: str, excluded: Excluded) -> UpdateResult:
        """
        Checks if an `Excluded` entry with a given mbid exists in the `excluded` list of a RequestsCache document.
        If it exists, updates it; otherwise, adds it as a new entry.

        Args:
            cache_id (str): The ObjectId of the RequestsCache entry to update.
            excluded (Excluded): The Excluded entry to add or update.

        Returns:
            UpdateResult: The result of the update operation.
        """
        # Check if an entry with the same mbid already exists in the `excluded` list
        existing_excluded = self.collection.find_one(
            {"_id": ObjectId(cache_id), "excluded.mbid": excluded.mbid},
            {"excluded.$": 1}
        )

        if existing_excluded:
            # If an entry with this mbid exists, update it
            return self.collection.update_one(
                {"_id": ObjectId(cache_id), "excluded.mbid": excluded.mbid},
                {"$set": {"excluded.$": excluded.model_dump(by_alias=True)}}
            )
        else:
            # If no such entry exists, add it as a new entry
            return self.add_excluded_entry(cache_id, excluded)
