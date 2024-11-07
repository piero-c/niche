# Module for the final playlist
from src.auth.SpotifyUser import SpotifyUser
from typing import TypedDict
from src.db.DB import DB
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.db.DAOs.RequestsDAO import RequestDAO
from src.models.pydantic.Playlist import Playlist as PlaylistModel
from src.services._shared_classes.PlaylistRequest import PlaylistRequest
from pathlib import Path


COVER_IMAGE_PATH = Path('../assets/icon.jpg')

class NicheTrack(TypedDict):
    """Niche track obj

    Args:
        TypedDict
    """
    artist     : str
    artist_id  : str
    track      : str
    spotify_uri: str
    spotify_url: str

# Playlist Class (FOR GENERATION PURPOSES ONLY)
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
        playlist_info = req.get_playlist_info()

        # Create a new playlist with placeholder name and description
        playlist = spotify_user.execute(
            'user_playlist_create',
            user          = spotify_user.id,
            name          = playlist_info['name'],
            public        = True,
            description   = playlist_info['description'],
            collaborative = False
        )

        # Extract Spotify URIs from the provided tracks
        track_uris = [track.get('spotify_uri') for track in tracks if 'spotify_uri' in track]

        # Add the extracted tracks to the newly created playlist
        # Spotify API allows adding up to 100 tracks per request
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            spotify_user.execute('playlist_add_items', playlist_id=playlist['id'], items=batch)

        # Store playlist information as attributes
        self.id          = playlist['id']
        self.url         = playlist['external_urls']['spotify']
        self.name        = playlist['name']
        self.description = playlist['description']
        self.length      = len(tracks)

        spotify_user.upload_playlist_cover_image(COVER_IMAGE_PATH)

        self.user_oid = spotify_user.oid
        self.request_oid = req.request_oid

        db = DB()
        dao = PlaylistDAO(db)
        entry = dao.create(
            PlaylistModel(
                user=self.user_oid,
                name=self.name,
                request=self.request_oid,
                link=self.url,
                generated_length=self.length
            )
        )
        self.oid = entry.inserted_id

        rdao = RequestDAO(db)
        rdao.update(
            document_id=req.request_oid,
            update_data={
                'playlist_generated': entry.inserted_id
            }
        )

    def add_track(self, uri: str, spotify_user: SpotifyUser) -> None:
        """_summary_

        Args:
            uri (str): _description_
            spotify_user (SpotifyUser): _description_
        """
        # STEP 1: Update plaulist on spotify
        spotify_user.execute('playlist_add_items', playlist_id=self.id, items=[uri])
        # STEP 2: Update playlist object
        self.length += 1
        # STEP 3: 
        db = DB()
        dao = PlaylistDAO(db)
        dao.update(
            self.oid, 
            { 'generated_length': self.length }
        )
        return (None)
    
    def delete(self, user: SpotifyUser) -> None:
        """_summary_

        Args:
            user (SpotifyUser): _description_

        Returns:
            bool: _description_
        """
        # STEP 1: Delete playlist on spotify
        user.execute('user_playlist_unfollow', user=user.id, playlist_id=self.id)

        # STEP 2: Delete link from requests
        db = DB()
        rdao = RequestDAO(db)
        rdao.update(self.request_oid, {'playlist_generated': None})

        # STEP 3: Delete entry in playlists collection
        pdao = PlaylistDAO(db)
        pdao.delete(self.oid)

        return(None)

