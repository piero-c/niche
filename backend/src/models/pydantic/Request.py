from pydantic import BaseModel, Field
from typing import Optional
from models.pydantic.BaseSchema import BaseSchema, PyObjectId

class Params(BaseModel):
    songs_min_year_created: Optional[int] = None
    songs_length_min_secs: int
    songs_length_max_secs: int
    language: str
    genre: str
    niche_level: str

    class Config:
        json_schema_extra = {
            "example": {
                "songs_min_year_created": 2000,
                "songs_length_min_secs": 180,
                "songs_length_max_secs": 300,
                "language": "English",
                "genre": "pop",
                "niche_level": "Very"
            }
        }

class Stats(BaseModel):
    percent_artists_valid: Optional[float] = None
    average_artist_followers: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                'percent_artists_valid': 2,
                'average_artist_followers': 2000
            }
        }

class Request(BaseSchema):
    user: PyObjectId
    params: Params
    playlist_generated: Optional[PyObjectId] = None
    stats: Stats = Field(default_factory=Stats)

    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "user": "60d5ec49f8d2e30f8c8f9e4a",
                "params": {
                    "songs_min_year_created": 2000,
                    "songs_length_min_secs": 180,
                    "songs_length_max_secs": 300,
                    "language": "English",
                    "genre": "Pop",
                    "niche_level": "Mainstream",
                    "playlist_length": "Long"
                },
                "playlist_generated": "60d5ec49f8d2e30f8c8f9e4b"
            }
        }
