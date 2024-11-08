from src.models.pydantic.BaseSchema import BaseSchema, PyObjectId
from typing import Optional

class Playlist(BaseSchema):
    user                 : PyObjectId
    name                 : str
    request              : PyObjectId
    link                 : str
    generated_length     : int
    time_to_generate_mins: Optional[float] = None

    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "user"                 : "60d5ec49f8d2e30f8c8f9e4a",
                "name"                 : "My Playlist",
                "request"              : "60d5ec49f8d2e30f8c8f9e4b",
                "link"                 : "http://example.com/playlist",
                "generated_length"     : 20,
                "time_to_generate_mins": 12
            }
        }
