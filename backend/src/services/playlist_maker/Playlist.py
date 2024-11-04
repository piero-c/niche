# Module for the final playlist
from auth.SpotifyUser import SpotifyUser
from typing import TypedDict
from db.DB import DB
from db.DAOs.PlaylistsDAO import PlaylistDAO
from db.DAOs.RequestsDAO import RequestDAO
from models.pydantic.Playlist import Playlist as PlaylistModel
from services.playlist_maker.PlaylistRequest import PlaylistRequest
from PIL import Image  # You may need to install Pillow if not already installed
import io
import base64
from pathlib import Path

from utils.logger import logger
import requests

COVER_IMAGE_PATH = Path('../../assets/icon.jpg')

# TODO - still return the playlist if not enough songs - Deal with the error throwing at middleware level?
class NicheTrack(TypedDict):
    """Niche track obj

    Args:
        TypedDict
    """
    artist     : str
    track      : str
    spotify_uri: str
    spotify_url: str

# Playlist Class
class Playlist:
    """Playlist Object

    Attributes:
        id (str): Spotify Playlist ID.
        url (str): Spotify Playlist URL.
        name (str): Name of the playlist.
        description (str): Description of the playlist.
    """
    def __init__(self, tracks: list[NicheTrack], req: PlaylistRequest, spotify_user: SpotifyUser) -> None:
        """Initialize the playlist

        Args:
            tracks (list[NicheTrack]): The tracks to add
            req (PlaylistRequest): The request that was used to generate the playlist
            user (SpotifyUser): The Spotify Authenticated User
        """
        # Extract Spotify URIs from the provided tracks
        track_uris = [track.get('spotify_uri') for track in tracks if 'spotify_uri' in track]

        playlist_info = req.get_playlist_info()

        # Create a new playlist with placeholder name and description
        playlist = spotify_user.client.user_playlist_create(
            user          = spotify_user.id,
            name          = playlist_info['name'],
            public        = True,
            description   = playlist_info['description'],
            collaborative = False
        )

        # Add the extracted tracks to the newly created playlist
        # Spotify API allows adding up to 100 tracks per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            spotify_user.client.playlist_add_items(playlist_id=playlist['id'], items=batch)

        # Store playlist information as attributes
        self.id          = playlist['id']
        self.url         = playlist['external_urls']['spotify']
        self.name        = playlist['name']
        self.description = playlist['description']
        self.length      = len(tracks)

        self._upload_cover_image(spotify_user)

        user_oid = spotify_user.oid
        request_oid = req.request_oid

        db = DB()
        dao = PlaylistDAO(db)
        entry = dao.create(
            PlaylistModel(
                user=user_oid,
                name=self.name,
                request=request_oid,
                link=self.url,
                length=self.length
            )
        )

        rdao = RequestDAO(db)
        rdao.update(
            document_id=req.request_oid,
            update_data={
                'playlist_generated': entry.inserted_id
            }
        )

    def _upload_cover_image(self, spotify_user: SpotifyUser) -> None:
        # Open the image and convert it to a base64-encoded JPEG
        with Image.open(COVER_IMAGE_PATH) as img:
            img = img.convert("RGB")  # Ensure the image is in RGB format
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        try:
            spotify_user.client.playlist_upload_cover_image(self.id, image_base64)
        except requests.exceptions.ReadTimeout:
            # Handle the timeout exception as needed
            logger.error("Timeout occurred while uploading the cover image. Please try again later.")