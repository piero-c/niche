# artist_dao.py

from typing import List, Optional
from bson import ObjectId
from mongoengine import DoesNotExist
from models.Artist import Artist
from utils.logger import logger


class ArtistsDAO:
    """Artist Data Access Object using MongoEngine."""

    def get_artist(self, artist_id: ObjectId) -> Optional[Artist]:
        """
        Retrieve an artist by their ObjectId.

        Args:
            artist_id (ObjectId): The unique identifier of the artist.

        Returns:
            Optional[Artist]: The artist object if found, else None.
        """
        try:
            artist = Artist.objects(id=artist_id).get()
            logger.info(f"Artist found: {artist}")
            return artist
        except DoesNotExist:
            logger.warning(f"Artist with id {artist_id} does not exist.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving artist with id {artist_id}: {e}")
            return None

    def get_artists_in_genre(self, genre: str) -> List[Artist]:
        """
        Retrieve all artists within a specific genre.

        Args:
            genre (str): The genre to filter artists by.

        Returns:
            List[Artist]: A list of artists belonging to the specified genre.
        """
        try:
            artists = Artist.objects(genres__name=genre)
            logger.info(f"Found {artists.count()} artists in genre '{genre}'.")
            return list(artists)
        except Exception as e:
            logger.error(f"Error retrieving artists in genre '{genre}': {e}")
            return []
