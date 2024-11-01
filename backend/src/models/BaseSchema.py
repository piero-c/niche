import os
import json
from mongoengine import Document, StringField, DateTimeField, signals
from datetime import datetime, timezone

# Load configuration from config.json
with open('../../config/config.json', 'r') as config_file:
    config = json.load(config_file)

# Get the environment variable
ENV = os.environ.get('ENV')
if not ENV:
    raise EnvironmentError("Please specify an environment")

cfg = config.get(ENV)
if not cfg:
    raise KeyError(f"Configuration for environment '{ENV}' not found")

# Define the BaseSchema
class BaseSchema(Document):
    created_at = DateTimeField(default=datetime.now(timezone.utc), required=True)
    updated_at = DateTimeField(default=datetime.now(timezone.utc), required=True)
    created_by = StringField(default=cfg['user'], required=True)
    updated_by = StringField(default=cfg['user'], required=True)

    meta = {
        'abstract': True,  # This makes BaseSchema an abstract base class
        'timestamps': True  # Note: 'timestamps' is not a MongoEngine option, included for clarity
    }

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        """Signal to update 'updated_at' before saving"""
        document.updated_at = datetime.now(timezone.utc)

# Connect the pre_save signal to the BaseSchema
signals.pre_save.connect(BaseSchema.pre_save, sender=BaseSchema)
