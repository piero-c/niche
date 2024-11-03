# models/RequestsCache.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from models.pydantic.BaseSchema import BaseSchema
from enum import Enum
from bidict import bidict

ReasonExcluded = Enum('ReasonExcluded', ['TOO_MANY_SOMETHING', 'NOT_LIKED_ENOUGH', 'WRONG_LANGUAGE', 'TOO_FEW_SOMETHING'] )
REASONMAP: bidict = bidict({
    ReasonExcluded.TOO_MANY_SOMETHING: "Too Many Followers / Listeners / Plays",
    ReasonExcluded.NOT_LIKED_ENOUGH  : "Ratio of Listeners to Plays Too Small",
    ReasonExcluded.WRONG_LANGUAGE    : "Artist Does Not Sing in the Requested Language",
    ReasonExcluded.TOO_FEW_SOMETHING : "Too Few Followers / Listeners / Plays"
})

class Excluded(BaseModel):
    name: Optional[str] = None
    mbid: str
    reason_excluded: str
    date_excluded: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_schema_extra = {
            "example": {
                "mbid": "12345",
                "reason_excluded": "Too Few Followers / Listeners / Plays",
                "date_excluded": "2024-04-27T12:34:56Z"
            }
        }

class ParamsCache(BaseModel):
    language: str
    genre: str
    niche_level: str

    class Config:
        json_schema_extra = {
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
        json_schema_extra = {
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
