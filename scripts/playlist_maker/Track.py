from scripts.utils.util import convert_ms_to_s
from scripts.utils.spotify_util import SpotifyTrack
from scripts.utils.lastfm_util import LastFMTrack
from scripts.auth_objects.SpotifyUser import SpotifyUser
from scripts.utils.logger import logger

class Track:
    """High level Track

    Attributes:
        name
        artist
        user
        spotify_track
            Requires call: attach_spotify_track_information
        spotify_uri
            Requires call: attach_spotify_track_information 
        spotify_url
            Requires call: attach_spotify_track_information 
        track_length_seconds
            Requires call: attach_spotify_track_information 
    """
    def __init__(self, name: str, artist: str, user: SpotifyUser) -> None:
        """Initialize the track

        Args:
            name (str): Track name
            artist (str): Track artist
            user (SpotifyUser): Spotify Authenticated User
        """
        self.name   = name
        self.artist = artist
        self.user   = user

    @classmethod
    def from_lastfm(cls, lastfm_track: LastFMTrack, user: SpotifyUser) -> 'Track':
        """Create track from lastfm

        Args:
            lastfm_track (LastFMTrack): Track as returned by lastfm
            user (SpotifyUser): Spotify Authenticated User

        Raises:
            Exception: Invalid track object or user

        Returns:
            Track: Track
        """
        try:
            name        = lastfm_track.get('name', "")
            artist_name = lastfm_track.get('artist', {}).get('name', "")
            track       = cls(name, artist_name, user)
            return(track)
        except Exception as e:
            raise Exception(f"Couldn't create track {name} by {artist_name} from lastfm: {e}")

    def attach_spotify_track_information(self, spotify_artist_id = "") -> SpotifyTrack:
        """Attach information about the track from spotify

        Raises:
            Exception: Unexpected error
            Exception: Couldn't find track

        Returns:
            SpotifyTrack: Track as returned by spotify
        """
        # Return existing Spotify track information if already attached
        if(getattr(self, 'spotify_track', None)):
            return(self.spotify_track)

        spotify_track = None
        try:
            spotify_tracks = self.user.get_spotify_tracks_direct(self.name, self.artist)
            spotify_track = spotify_tracks[0]
        except Exception as e:
            logger.warning(f"Couldn't get Spotify track information for '{self.name}' by '{self.artist}' with direct search: {e}")
        
        if(not spotify_track):
            try:
                spotify_track = self.user.get_spotify_track_fuzzy(self.name, self.artist)
            except Exception as e:
                logger.warning(f"Couldn't get Spotify track information for '{self.name}' by '{self.artist}' with fuzzy search: {e}")

        if(spotify_track):
            try:
                # Attach the Spotify track information to the current object
                self.spotify_track        = spotify_track
                self.spotify_uri          = spotify_track.get('uri', '')
                self.spotify_url          = spotify_track.get('external_urls', {}).get('spotify', '')
                self.track_length_seconds = convert_ms_to_s(spotify_track.get('duration_ms', 0))

                return(self.spotify_track)
            except Exception as e:
                raise Exception(f"Unexpected error when attaching track {self.name} by {self.artist}: {e}")
            
        raise Exception(f"Couldn\'t find track {self.name} by {self.artist} on Spotify.")
        
    def artist_id_in_spotify_track(self, artist_id: str) -> bool:
        """Check if the artist id is in the track

        Args:
            artist_id (str): Spotify artist id to check

        Returns:
            bool: Is it in the track?
        """
        if (not hasattr(self, 'spotify_track')):
            self.attach_spotify_track_information()
        for artist in self.spotify_track.get('artists', [{}]):
            if(artist.get('id') == artist_id):
                return(True)
        
        return(False)
