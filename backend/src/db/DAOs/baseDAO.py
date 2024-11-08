from typing             import Type, TypeVar, Generic, Optional, Dict, Any
from pymongo.collection import Collection
from pymongo.results    import InsertOneResult, UpdateResult, DeleteResult
from pydantic           import BaseModel, ValidationError
from bson               import ObjectId


# Define a generic type variable for the data model
T = TypeVar("T", bound=BaseModel)

class BaseDAO(Generic[T]):
    """
    Base Data Access Object that provides CRUD operations.
    """

    def __init__(self, collection: Collection, model: Type[T]) -> None:
        """
        Initializes the BaseDAO with a MongoDB collection and a Pydantic model.

        Args:
            collection (Collection): The MongoDB collection to operate on.
            model (Type[T]): The Pydantic model class representing the document schema.
        """
        self.collection = collection
        self.model = model

    def create(self, data: T) -> InsertOneResult:
        """Inserts a new document into the collection."""
        try:
            return self.collection.insert_one(data.model_dump(by_alias=True))
        except ValidationError as e:
            raise ValueError(f"Data validation error: {e}")

    def read_by_id(self, document_id: str) -> Optional[T]:
        """Retrieves a document by its ObjectId."""
        raw_data = self.collection.find_one({"_id": ObjectId(document_id)})
        return self.model(**raw_data) if raw_data else None

    def update(self, document_id: str, update_data: Dict[str, Any]) -> UpdateResult:
        """
        Updates a document by its ObjectId, validating `update_data` without enforcing required fields.

        Args:
            document_id (str): The ObjectId of the document to update.
            update_data (Dict[str, Any]): The data to update.

        Returns:
            UpdateResult: The result of the update operation.
        """
        # Filter to include only mutable, valid model fields
        clean_data = {k: v for k, v in update_data.items() if k in self.model.model_fields}

        # Use `construct` to create a model instance without enforcing required fields
        try:
            validated_instance = self.model.model_construct(**clean_data)
            # Create a set of fields to include: fields provided in `update_data` + default-set fields
            fields_to_include = set(clean_data.keys()).union({"updated_at", "updated_by"})
            
            # Convert to dict, ensuring only the specified fields are included
            validated_data = validated_instance.model_dump(exclude_unset=True, include=fields_to_include)
        except ValidationError as e:
            raise ValueError(f"Update data validation error: {e}")

        # Perform the update
        return self.collection.update_one({"_id": ObjectId(document_id)}, {"$set": validated_data})

    def delete(self, document_id: str) -> DeleteResult:
        """Deletes a document by its ObjectId."""
        return self.collection.delete_one({"_id": ObjectId(document_id)})
