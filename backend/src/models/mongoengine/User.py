# User.py

from mongoengine import StringField
from models.mongoengine.BaseSchema import BaseSchema

class User(BaseSchema):
    display_name = StringField(required=True)
    spotify_id   = StringField(required=True)

    meta = {
        'collection': 'users'  # Specifies the MongoDB collection name
    }
