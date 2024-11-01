from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from bson import ObjectId
from models.pydantic.Request import Request
from db.DB import DB

class RequestDAO:
    """
    Data Access Object for Request collection.

    Provides methods to create, read, update, and delete Request data in MongoDB.
    """

    def __init__(self, db: DB) -> None:
        """
        Initializes the RequestDAO with a database instance.

        Args:
            db (DB): The database instance.
        """
        self.collection: Collection = db.get_collection("requests")

    def create(self, request: Request) -> InsertOneResult:
        """
        Inserts a new request document into the collection.

        Args:
            request (Request): The request data to insert.

        Returns:
            InsertOneResult: The result of the insertion operation.
        """
        return (self.collection.insert_one(request.model_dump(by_alias=True)))

    def read_by_id(self, request_id: str) -> Optional[Request]:
        """
        Reads a request by its ObjectId.

        Args:
            request_id (str): The ObjectId of the request to find.

        Returns:
            Optional[Request]: The found request, or None if not found.
        """
        raw_data = self.collection.find_one({"_id": ObjectId(request_id)})
        return (Request.model_validate(raw_data) if (raw_data) else None)

    def read_all(self, filter: dict = {}) -> List[Request]:
        """
        Reads all requests matching a filter.

        Args:
            filter (dict): The filter criteria for finding requests.

        Returns:
            List[Request]: A list of matching requests.
        """
        documents = self.collection.find(filter)
        return ([Request.model_validate(doc) for doc in documents])

    def read_by_params(self, params: Dict[str, Any]) -> List[Request]:
        """
        Reads requests based on specific parameters within the `params` field.

        Args:
            params (Dict[str, Any]): The parameters to match in the `params` field of the requests.

        Returns:
            List[Request]: A list of requests that match the given parameters.
        """
        query = {f"params.{key}": value for key, value in params.items()}
        documents = self.collection.find(query)
        return ([Request.model_validate(doc) for doc in documents])

    def update(self, request_id: str, update_data: dict) -> UpdateResult:
        """
        Updates a request document by its ObjectId.

        Args:
            request_id (str): The ObjectId of the request to update.
            update_data (dict): The data to update in the request document.

        Returns:
            UpdateResult: The result of the update operation.
        """
        return (self.collection.update_one({"_id": ObjectId(request_id)}, {"$set": update_data}))

    def delete(self, request_id: str) -> DeleteResult:
        """
        Deletes a request document by its ObjectId.

        Args:
            request_id (str): The ObjectId of the request to delete.

        Returns:
            DeleteResult: The result of the delete operation.
        """
        return (self.collection.delete_one({"_id": ObjectId(request_id)}))
