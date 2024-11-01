# Playlist.py

from mongoengine import StringField, ReferenceField
from models.BaseSchema import BaseSchema

class Playlist(BaseSchema):
    user    = ReferenceField('users', required=True)
    name    = StringField(required=True)
    request = ReferenceField('requests', null=True)
    link    = StringField(required=True)

    meta = {
        'collection': 'playlists'  # Optional: specify the collection name
    }
