# models/BaseSchema.py

from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime, timezone
from db.config_loader import load_config

# Load configuration (ensure this is done outside the model to avoid side effects)
config = load_config()

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema_(cls, field_schema):
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
