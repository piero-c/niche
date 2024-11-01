# db.py

from mongoengine import connect
from mongoengine.connection import get_db
from typing import ClassVar, Optional, Type
from db.config_loader import load_config
from utils.logger import logger

class DB:
    """
    Singleton class to manage MongoDB connection using MongoEngine.
    """
    _instance: ClassVar[Optional['DB']] = None

    def __new__(cls: Type['DB']) -> 'DB':
        """
        Create a new instance of DB if one doesn't exist.

        Returns:
            DB: The singleton instance of the DB class.
        """
        if cls._instance is None:
            config: dict = load_config()
            mongo_uri: str = config['MONGO_URI']
            cls._instance = super(DB, cls).__new__(cls)
            logger.info("Connecting to MongoDB...")
            try:
                connect(host=mongo_uri)
                logger.info("Successfully connected to MongoDB!")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise e
        return cls._instance

    def get_database(self):
        """
        Get the default MongoDB database.

        Returns:
            Database: The default MongoDB database instance.
        """
        return get_db()

    # Optional: If you still need to access raw collections
    def get_collection(self, name: str):
        """
        Get a raw MongoDB collection.

        Args:
            name (str): The name of the collection.

        Returns:
            Collection: The MongoDB collection instance.
        """
        return self.get_database()[name]
