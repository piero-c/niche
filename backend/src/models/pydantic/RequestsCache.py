# models/RequestsCache.py

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone
from models.pydantic.BaseSchema import BaseSchema

class Excluded(BaseModel):
    mbid: str
    reason_excluded: str
    date_excluded: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_schema_extra = {
            "example": {
                "mbid": "12345",
                "reason_excluded": "Genre mismatch",
                "date_excluded": "2024-04-27T12:34:56Z"
            }
        }

class ParamsCache(BaseModel):
    language: str
    genre: str
    niche_level: str

    class Config:
        schema_extra = {
            "example": {
                "language": "English",
                "genre": "Pop",
                "niche_level": "Mainstream"
            }
        }

class RequestsCache(BaseSchema):
    params: ParamsCache
    excluded: List[Excluded]

    class Config(BaseSchema.Config):
        schema_extra = {
            "example": {
                "params": {
                    "language": "English",
                    "genre": "Pop",
                    "niche_level": "Mainstream"
                },
                "excluded": [
                    {
                        "mbid": "12345",
                        "reason_excluded": "Genre mismatch",
                        "date_excluded": "2024-04-27T12:34:56Z"
                    },
                    {
                        "mbid": "67890",
                        "reason_excluded": "Language mismatch",
                        "date_excluded": "2024-04-28T08:20:30Z"
                    }
                ]
            }
        }
