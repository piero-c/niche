# user.py

from mongoengine import StringField
from BaseSchema import BaseSchema

class User(BaseSchema):
    display_name = StringField(required=True)
    spotify_id   = StringField(required=True)

    meta = {
        'collection': 'users'  # Specifies the MongoDB collection name
    }
