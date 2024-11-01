# artist_dao.py

from db import DB
from pymongo.collection import Collection
from bson.objectid import ObjectId

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

    def create_artist(self, name: str, genre: str) -> ObjectId:
        artist: dict[str, any] = {
            'name': name,
            'genre': genre
        }
        result = self.collection.insert_one(artist)
        return(result.inserted_id)

    def update_artist(self, artist_id: ObjectId, update_fields: dict[str, any]) -> int:
        result = self.collection.update_one(
            {'_id': artist_id},
            {'$set': update_fields}
        )
        return(result.modified_count)

    def delete_artist(self, artist_id: ObjectId) -> int:
        result = self.collection.delete_one({'_id': artist_id})
        return(result.deleted_count)
    
    def get_artists_in_genre(self, genre: str) -> list[dict[str, any]]:
        """Get all artists which are in a certain genre

        Args:
            genre (str): The genre

        Returns:
            list[dict[str, any]]: The artists as returned by mongo
        """
        return(self.collection.find({'genres.name': genre}))

