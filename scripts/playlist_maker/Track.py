from scripts.utils.util import convert_ms_to_s
from scripts.utils.spotify_util import SpotifyTrack
from scripts.auth_objects.SpotifyUser import SpotifyUser

class Track:
    """_summary_
    """
    def __init__(self, name: str, artist: str, user: SpotifyUser) -> None:
        """_summary_

        Args:
            name (str): _description_
            artist (str): _description_
        """
        self.name   = name
        self.artist = artist
        self.user   = user

    @classmethod
    def from_lastfm(cls, lastfm_track: dict, user: SpotifyUser) -> 'Track':
        """_summary_

        Args:
            lastfm_track (dict): _description_

        Returns:
            Track: _description_
        """
        try:
            name        = lastfm_track.get('name', "")
            artist_name = lastfm_track.get('artist', {}).get('name', "")
            track       = cls(name, artist_name, user)
            return track
        except Exception as e:
            raise Exception(f"Couldn't create track {name} by {artist_name} from lastfm: {e}")

    def attach_spotify_track_information(self) -> SpotifyTrack:
        # Return existing Spotify track information if already attached
        if getattr(self, 'spotify_track', None):
            return(self.spotify_track)

        spotify_track = None
        try:
            spotify_tracks = self.user.get_spotify_tracks_direct(self.name, self.artist)
            spotify_track = spotify_tracks[0]
        except Exception as e:
            print(f"Couldn't get Spotify track information for '{self.name}' by '{self.artist}' with direct search: {e}")
        
        if (not spotify_track):
            try:
                spotify_track = self.user.get_spotify_track_fuzzy(self.name, self.artist)
            except Exception as e:
                print(f"Couldn't get Spotify track information for '{self.name}' by '{self.artist}' with fuzzy search: {e}")

        if (spotify_track):
            try:
                # Attach the Spotify track information to the current object
                self.spotify_track = spotify_track
                self.spotify_uri = spotify_track.get('uri', '')
                self.spotify_url = spotify_track.get('external_urls', {}).get('spotify', '')
                self.track_length_seconds = convert_ms_to_s(spotify_track.get('duration_ms', 0))
                return(self.spotify_track)
            except Exception as e:
                raise Exception(f"Unexpected error when attaching track {self.name} by {self.artist}: {e}")
            
        raise Exception(f"Couldn\'t find track {self.name} by {self.artist} on Spotify.")
        
    def artist_id_in_spotify_track(self, artist_id: str) -> bool:
        assert(hasattr(self, 'spotify_track'))
        for artist in self.spotify_track.get('artists', [{}]):
            if (artist.get('id') == artist_id):
                return(True)
        
        return(False)
            
        