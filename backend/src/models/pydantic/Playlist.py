from src.models.pydantic.BaseSchema import BaseSchema, PyObjectId

class Playlist(BaseSchema):
    user: PyObjectId
    name: str
    request: PyObjectId
    link: str
    generated_length: int

    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "user": "60d5ec49f8d2e30f8c8f9e4a",
                "name": "My Playlist",
                "request": "60d5ec49f8d2e30f8c8f9e4b",
                "link": "http://example.com/playlist"
            }
        }
