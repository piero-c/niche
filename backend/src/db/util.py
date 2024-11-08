from typing import Union
from pymongo.results import InsertOneResult, UpdateResult
from bson import ObjectId
from src.models.pydantic.BaseSchema import PyObjectId  # Import your PyObjectId

class OperationResult:
    """
    Wrapper class to encapsulate the result of a MongoDB insert or update operation,
    providing a unified interface for accessing the document's PyObjectId.
    """

    def __init__(self, result: Union[InsertOneResult, UpdateResult], object_id: ObjectId):
        self.result = result
        self.object_id = PyObjectId(object_id)  # Convert ObjectId to PyObjectId

    @property
    def id(self) -> PyObjectId:
        return self.object_id
