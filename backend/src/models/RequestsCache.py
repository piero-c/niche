# requestsCache.py

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
    DateTimeField
)
from datetime import datetime, timezone
from BaseSchema import BaseSchema

class Excluded(EmbeddedDocument):
    mbid            = StringField(required=True)
    reason_excluded = StringField(required=True)
    date_excluded   = DateTimeField(default=datetime.now(timezone.utc), required=True)

class ParamsCache(EmbeddedDocument):
    language    = StringField(required=True)
    genre       = StringField(required=True)
    niche_level = StringField(required=True)

class RequestsCache(BaseSchema):
    params   = EmbeddedDocumentField(ParamsCache)
    excluded = ListField(EmbeddedDocumentField(Excluded))

    meta = {
        'collection': 'requests',
        'indexes'   : [
            {'fields': ['params.language']},
            {'fields': ['params.genre']},
            {'fields': ['params.niche_level']}
        ]
    }

