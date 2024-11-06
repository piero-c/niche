# artist_dao.py

from src.db.DB import DB
from pymongo.collection import Collection
from bson.objectid import ObjectId
from pymongo.synchronous.cursor import Cursor

class ArtistsDAO:
    """Artist Data Access Object
    """
    def __init__(self, db: DB) -> None:
        """Initialize the DAO

        Args:
            db (DB): The DB
        """
        self.collection: Collection = db.get_collection('artists')

    def get_artist(self, artist_id: ObjectId) -> dict[str, any]:
        return(self.collection.find_one({'_id': artist_id}))

    def get_artists_in_genre(self, genre: str) -> Cursor:
        """Get all artists which are in a certain genre

        Args:
            genre (str): The genre

        Returns:
            list[dict[str, any]]: The artists as returned by mongo
        """
        return(self.collection.find({'genres.name': genre}))

    def count_artists_in_genre(self, genre: str) -> int:
        """Count all artists that belong to a certain genre.

        Args:
            genre (str): The genre to count artists in.

        Returns:
            int: The count of artists in the specified genre.
        """
        return(self.collection.count_documents({'genres.name': genre}))
