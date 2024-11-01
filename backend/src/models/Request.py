from mongoengine import EmbeddedDocument, EmbeddedDocumentField, StringField, IntField, ReferenceField
from models.BaseSchema import BaseSchema

class Params(EmbeddedDocument):
    songs_min_year_created = IntField()
    songs_length_min_secs  = IntField(required=True)
    songs_length_max_secs  = IntField(required=True)
    language               = StringField(required=True)
    genre                  = StringField(required=True)
    niche_level            = StringField(required=True)
    playlist_length        = StringField(required=True)

class Request(BaseSchema):
    user                = ReferenceField('users', required=True)
    params              = EmbeddedDocumentField(Params, required=True)
    playlist_generated  = ReferenceField('playlists')

    meta = {
        'collection': 'requests'
    }
