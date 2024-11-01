# Artist.py

from mongoengine import (
    DynamicDocument
)
from models.mongoengine.BaseSchema import BaseSchema

class Artist(BaseSchema, DynamicDocument):
    meta = {
        'collection': 'artists',
        'indexes': [
            {'fields': ['genres.name']}
        ]
    }
