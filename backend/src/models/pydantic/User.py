# models/User.py

from models.pydantic.BaseSchema import BaseSchema

class User(BaseSchema):
    display_name: str
    spotify_id: str

    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "display_name": "John Doe",
                "spotify_id": "spotify123456"
            }
        }
