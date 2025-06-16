from pydantic import ConfigDict
from src.models.pydantic.BaseSchema import BaseSchema

class User(BaseSchema):
    display_name: str
    spotify_id  : str

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "display_name": "John Doe",
                "spotify_id"  : "spotify123456"
            }
        }
    )

