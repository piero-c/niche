# models/BaseSchema.py

from pydantic      import BaseModel, Field, ConfigDict, GetCoreSchemaHandler, field_serializer
from pydantic_core import core_schema

from bson     import ObjectId

from datetime import datetime, timezone

from src.db.config_loader import load_config

# Load configuration (ensure this is done outside the model to avoid side effects)
config = load_config()

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        def validate(value):
            if isinstance(value, ObjectId):
                return value
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)
        return core_schema.no_info_plain_validator_function(
            function=validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return handler(core_schema.str_schema())


class BaseSchema(BaseModel):
    id         : PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime    = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime    = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str         = Field(default=config.get('user'))
    updated_by: str         = Field(default=config.get('user'))
    v          : int        = Field(default=0, alias="__v")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    @field_serializer("id")
    def serialize_id(self, id_value):
        return str(id_value)
    
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
