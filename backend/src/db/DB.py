# db.py

from pymongo            import MongoClient
from pymongo.collection import Collection
from pymongo.database   import Database
from typing             import Optional, Type, ClassVar

from src.db.config_loader import load_config
from src.utils.logger     import logger

class DB:
    """The DB
    """
    _instance: ClassVar[Optional['DB']] = None

    client: MongoClient
    db: Database

    def __new__(cls: Type['DB']) -> 'DB':
        """Make a new DB

        Args:
            cls (Type[&#39;DB&#39;]): DB

        Returns:
            DB: The DB, based on env
        """
        if(cls._instance is None):
            config: dict[str, any] = load_config()
            mongo_uri: str = config['MONGO_URI']
            cls._instance = super(DB, cls).__new__(cls)
            logger.info("Connecting to DB...")
            cls._instance.client = MongoClient(mongo_uri)
            cls._instance.db = cls._instance.client.get_default_database()
            logger.info("Connected to DB!")
        return(cls._instance)

    def get_collection(self, name: str) -> Collection:
        """Get a collection from the DB

        Args:
            name (str): Collection Name

        Returns:
            Collection: The Collection
        """
        return(self.db[name])
    
    def close_connection(self):
        """Close the MongoDB connection."""
        if self.client:
            logger.info("Closing MongoDB connection.")
            self.client.close()