from src.utils.util import convert_ms_to_s
from src.utils.spotify_util import SpotifyTrack, find_exact_match
from src.utils.lastfm_util import LastFMTrack
from src.auth.SpotifyUser import SpotifyUser
from src.utils.logger import logger

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

    def _attach_valid_track(self, spotify_track: SpotifyTrack) -> SpotifyTrack:
        try:
            # Attach the Spotify track information to the current object
            self.spotify_track        = spotify_track
            self.spotify_uri          = spotify_track.get('uri', '')
            self.spotify_url          = spotify_track.get('external_urls', {}).get('spotify', '')
            self.track_length_seconds = convert_ms_to_s(spotify_track.get('duration_ms', 0))
            return(self.spotify_track)
        except Exception as e:
            raise Exception(f"Unexpected error when attaching track {self.name} by {self.artist}: {e}")

    def attach_spotify_track_information_from_spotify_track(self, spotify_track: SpotifyTrack, artist_spotify_id: str = "") -> SpotifyTrack:
        """_summary_

        Args:
            spotify_track (SpotifyTrack): _description_
            artist_spotify_id (str, optional): _description_. Defaults to "".

        Raises:
            Exception: _description_

        Returns:
            SpotifyTrack: _description_
        """
        # Return existing Spotify track information if already attached
        if(getattr(self, 'spotify_track', None)):
            return(self.spotify_track)

        if ((not artist_spotify_id) or self.artist_id_in_spotify_track(artist_spotify_id)):
            return (self._attach_valid_track(spotify_track))
        else:
            logger.error(f"Track {self.name} not by {self.artist} {artist_spotify_id}")

    def attach_spotify_track_information(self, artist_spotify_id: str = "") -> SpotifyTrack:
        """Attach information about the track from spotify

        Args:
            artist_spotify_id (str, Optional): The spotify id of the artist that made the track (for validation purposes). Default ""

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
        except Exception as e:
            logger.warning(f"Couldn't get Spotify track information for '{self.name}' by '{self.artist}' with direct search: {e}")

        spotify_track = find_exact_match(spotify_tracks, self.name, self.artist)

        if(spotify_track and ((not artist_spotify_id) or self.artist_id_in_spotify_track(artist_spotify_id))):
            return(self._attach_valid_track(spotify_track))
        else:
            logger.error(f"Track {self.name} not by {self.artist} {artist_spotify_id}")
            
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
    
    def is_original_with_lyrics(self) -> bool:
        """
        Determines if the track is original with lyrics by checking if its name
        does not contain any keywords indicating it's an instrumental, cover, or version.

        Returns:
            bool: True if original with lyrics, False otherwise.
        """
        keywords = ['instrumental', 'cover', 'inst.', 'cov.', 'ver.', 'version', 'dub', "background music", "no vocals",
        "alternative version", "soundtrack"]
        name_lower = self.name.lower()  # Convert to lowercase for case-insensitive comparison
        return not any(keyword in name_lower for keyword in keywords)


