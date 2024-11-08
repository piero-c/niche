# models/BaseSchema.py

from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime, timezone
from src.db.config_loader import load_config

# Load configuration (ensure this is done outside the model to avoid side effects)
config = load_config()

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, values=None, config=None, field=None):
        """
        Validates the given value, allowing it to be an ObjectId instance or a valid ObjectId string.
        
        Args:
            v: The value to validate.
            values: Optional additional values (ignored).
            config: Optional configuration (ignored).
            field: Optional field metadata (ignored).
        
        Returns:
            ObjectId: The validated ObjectId.
        
        Raises:
            ValueError: If the value is not a valid ObjectId.
        """
        if isinstance(v, ObjectId):
            return v
        elif isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId format")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class BaseSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default=config.get('user'))
    updated_by: str = Field(default=config.get('user'))
    v: int = Field(default=0, alias="__v")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
def clean_update_data(update_data: dict, exclude_fields: list[str] = ["_id", "created_at", "created_by"]) -> dict:
    """
    Removes fields that shouldn't be updated from the update data dictionary.

    Args:
        update_data (dict): The original update data.
        exclude_fields (List[str]): Fields to exclude from updates.

    Returns:
        dict: A clean update data dictionary with excluded fields removed.
    """
    return {k: v for k, v in update_data.items() if k not in exclude_fields}
