# db.py

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from scripts.db.config_loader import load_config
from typing import Optional, Type, ClassVar

class DB:
    _instance: ClassVar[Optional['DB']] = None

    client: MongoClient
    db: Database

    def __new__(cls: Type['DB']) -> 'DB':
        if cls._instance is None:
            config: dict[str, any] = load_config()
            mongo_uri: str = config['MONGO_URI']
            cls._instance = super(DB, cls).__new__(cls)
            print("Connecting to DB...")
            cls._instance.client = MongoClient(mongo_uri)
            cls._instance.db = cls._instance.client.get_default_database()
            print("Connected to DB!")
        return cls._instance

    def get_collection(self, name: str) -> Collection:
        return self.db[name]
