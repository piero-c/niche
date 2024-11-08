# models/RequestsCache.py

from pydantic import BaseModel, Field
from typing   import List, Optional
from datetime import datetime, timezone

from src.models.pydantic.BaseSchema import BaseSchema

class Excluded(BaseModel):
    name           : Optional[str] = None
    mbid           : str
    reason_excluded: str
    date_excluded  : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_schema_extra = {
            "example": {
                "name"           : "joe schmoe",
                "mbid"           : "12345",
                "reason_excluded": "Too Few Followers / Listeners / Plays",
                "date_excluded"  : "2024-04-27T12:34:56Z"
            }
        }

class ParamsCache(BaseModel):
    language   : str
    genre      : str
    niche_level: str

    class Config:
        json_schema_extra = {
            "example": {
                "language"   : "English",
                "genre"      : "Pop",
                "niche_level": "Very"
            }
        }

class RequestsCache(BaseSchema):
    params: ParamsCache
    excluded: List[Excluded]

    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "params": {
                    "language"   : "English",
                    "genre"      : "Pop",
                    "niche_level": "Very"
                },
                "excluded": [
                    {
                        "name"           : "joe schmoe",
                        "mbid"           : "12345",
                        "reason_excluded": "Too Few Followers / Listeners / Plays",
                        "date_excluded"  : "2024-04-27T12:34:56Z"
                    },
                    {
                        "name"           : "joe schmoe",
                        "mbid"           : "67890",
                        "reason_excluded": "Too Many Followers / Listeners / Plays",
                        "date_excluded"  : "2024-04-28T08:20:30Z"
                    }
                ]
            }
        }
