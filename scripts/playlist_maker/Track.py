from scripts.util import sleep, RequestType, convert_ms_to_s
from scripts.spotify_util import SpotifyTrack
import spotipy

class Track:
    """_summary_
    """
    def __init__(self, name: str, artist: str) -> None:
        """_summary_

        Args:
            name (str): _description_
            artist (str): _description_
        """
        self.name   = name
        self.artist = artist

    @classmethod
    def from_lastfm(cls, lastfm_track: dict) -> 'Track':
        """_summary_

        Args:
            lastfm_track (dict): _description_

        Returns:
            Track: _description_
        """
        try:
            name        = lastfm_track.get('name', "")
            artist_name = lastfm_track.get('artist', {}).get('name', "")
            track       = cls(name, artist_name)
            return track
        except:
            raise Exception(f"Couldn't create track {name} by {artist_name} from lastfm")
    
    def attach_spotify_track_information(self, spotipy_methods: spotipy.Spotify) -> SpotifyTrack:
        """_summary_

        Args:
            spotipy_methods (spotipy.Spotify): _description_

        Raises:
            Exception: _description_
            Exception: _description_

        Returns:
            SpotifyTrack: _description_
        """
        # TODO - HERE - impl some kind og fuzzy search (e.g. Harapan, pt.3 by the cottons vs part 3 (get results return top or see chat))
        if (getattr(self, 'spotify_track', None)):
            return (self.spotify_track)
        
        try:
            # Construct the search query
            query = f"track:{self.name} artist:{self.artist}"

            ## BEGIN REQUEST ##
            # Perform the search on Spotify for the track
            search_results = spotipy_methods.search(q=query, type='track', limit=1)
            sleep(RequestType.SPOTIFY)
            ## END REQUEST ##

            # Check if any tracks were found
            spotify_tracks = search_results.get('tracks', {}).get('items', [])
            if not spotify_tracks:
                print(f"No Spotify tracks found for '{self.name}' by '{self.artist}'.")
                raise Exception()

            # Get the first track from the search results
            spotify_track = spotify_tracks[0]

            self.spotify_track        = spotify_track
            self.spotify_uri          = spotify_track.get('uri', '')
            self.spotify_url          = spotify_track.get('external_urls', {}).get('spotify', '')
            self.track_length_seconds = convert_ms_to_s(spotify_track.get('duration_ms', 0))
        except:
            raise Exception(f'Couldn\'t get spotify track information for {self.name} by {self.artist}')

        return(self.spotify_track)