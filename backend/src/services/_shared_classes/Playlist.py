# Module for the final playlist
from src.db.DB import DB
from src.db.DAOs.PlaylistsDAO import PlaylistDAO
from src.db.DAOs.RequestsDAO import RequestDAO
from src.models.pydantic.Playlist import Playlist as PlaylistModel
from src.services._shared_classes.PlaylistRequest import PlaylistRequest
from src.auth.SpotifyUser import spotify_user
from pathlib import Path
from src.utils.spotify_util import NicheTrack


COVER_IMAGE_PATH = Path('../assets/icon.jpg')

# Playlist Class (FOR GENERATION PURPOSES ONLY)
class Playlist:
    """Playlist Object

    Attributes:
        id (str): Spotify Playlist ID.
        url (str): Spotify Playlist URL.
        name (str): Name of the playlist.
        description (str): Description of the playlist.
        oid
            Requires call: add_db_entry
        in_db
    """
    def __init__(self, tracks: list[NicheTrack], req: PlaylistRequest, add_to_db: bool = True) -> None:
        """Initialize the playlist

        Args:
            tracks (list[NicheTrack]): The tracks to add
            req (PlaylistRequest): The request that was used to generate the playlist
            add_to_db (bool, optional): Add the playlist to the db?. Default to true
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

        spotify_user.upload_playlist_cover_image(COVER_IMAGE_PATH, self.id)

        self.user_oid = spotify_user.oid
        self.request_oid = req.oid

        self.in_db = False
        if (add_to_db):
            self.add_db_entry()


    def add_db_entry(self) -> None:
        if (self.in_db):
            return (None)
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
            document_id=self.request_oid,
            update_data={
                'playlist_generated': entry.inserted_id
            }
        )
        self.in_db = True
        return(None)

    def add_track(self, uri: str) -> None:
        """_summary_

        Args:
            uri (str): _description_
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
    
    def delete(self) -> None:
        """_summary_

        Returns:
            bool: _description_
        """
        
        # STEP 1: Delete playlist on spotify
        spotify_user.execute('user_playlist_unfollow', user=spotify_user.id, playlist_id=self.id)

        # STEP 2: Delete link from requests
        db = DB()
        rdao = RequestDAO(db)
        rdao.update(self.request_oid, {'playlist_generated': None})

        # STEP 3: Delete entry in playlists collection
        pdao = PlaylistDAO(db)
        pdao.delete(self.oid)

        return(None)
    
    def add_generated_time(self, time_mins: float) -> None:
        db = DB()
        pdao = PlaylistDAO(db)
        pdao.update(self.oid, {'time_to_generate_mins': time_mins})

        return(None)

