from services.playlist_maker.Track import Track
from utils.util import strcomp
from utils.spotify_util import SpotifyArtist
from auth.LastFMRequests import LastFmArtist, LastFMRequests
from auth.SpotifyUser import SpotifyUser
from utils.musicbrainz_util import MusicBrainzArtist
from utils.logger import logger
class Artist:
    """Representing an artist, at a high level

    Attributes:
        name
        mbid
        user: Spotify Authenticated User
        lastfm: LastFM requests obj
        lastfm_artist: Artist as returned by lastfm
            Requires call: attach_artist_lastfm
        lastfm_artist_playcount: Artist playcount from lastfm
            Requires call: attach_artist_lastfm
        lastfm_artist_listeners: Artist listeners from lastfm
            Requires call: attach_artist_lastfm
        lastfm_artist_likeness: Calculated likeness based on lastfm playcount and listeners
            Requires call: attach_artist_lastfm
        lastfm_tracks: list of Track objects based on the artists top lastfm tracks
            Requires call: get_artist_top_tracks_lastfm
        spotify_artist_id
            Requires call: attach_spotify_artist_from_track
        spotify_artist: artist object as returned by spotify
            Requires call: attach_spotify_artist_from_track
        spotify_followers
            Requires call: attach_spotify_artist_from_track
        lastfm_tags
            Requires call: artist_in_lastfm_genre
    """
    def __init__(self, name: str, mbid: str, user: SpotifyUser) -> None:
        """Initialize the artist

        Args:
            name (str): Artist name
            mbid (str): Artist MBID
            user (SpotifyUser): Spotify Authenticated User
        """
        self.name   = name
        self.mbid   = mbid
        self.user   = user
        self.lastfm = LastFMRequests()

    @classmethod
    def from_musicbrainz(cls, musicbrainz_artist_object: MusicBrainzArtist, user: SpotifyUser) -> 'Artist':
        """Create artist from musicbrainz artist object

        Args:
            musicbrainz_artist_object (MusicBrainzArtist): Artist object as returned by musicbrainz
            user (SpotifyUser): Spotify Authenticated user

        Raises:
            Exception: If the musicbrainz artist is missing name or mbid or user invalid

        Returns:
            Artist: The artist
        """
        try:
            name = musicbrainz_artist_object.get('name', "")
            mbid = musicbrainz_artist_object.get('id', "")
            artist = cls(name, mbid, user)
            return(artist)
        except Exception as e:
            raise Exception(f'Could not create artist from musicbrainz for {name}: {e}')

    def _attach_lastfm_artist(self, artist: LastFmArtist) -> LastFmArtist:
        """Helper for attach lastfm artist
        """
        self.lastfm_artist           = artist.get('artist', None)
        self.lastfm_artist_playcount = int(self.lastfm_artist.get('stats', {}).get('playcount', 0))
        self.lastfm_artist_listeners = int(self.lastfm_artist.get('stats', {}).get('listeners', 0))
        self.lastfm_artist_likeness  = self.lastfm_artist_playcount / self.lastfm_artist_listeners if self.lastfm_artist_listeners else 0
        return(self.lastfm_artist)

    def _attach_top_tracks_lastfm(self, tracks: dict) -> list[Track]:
        """Helper for attach lastfm top tracks
        """
        tracks = tracks.get('toptracks', {}).get('track', [])
        valid_tracks = []
        for track in tracks:
            try:
                valid_tracks.append(Track.from_lastfm(track, self.user))
            except Exception as e:
                logger.error(e)
        
        self.lastfm_tracks = valid_tracks

        return(valid_tracks)

    def _get_tags_from_lastfm_artist(self) -> list[str]:
        """Helper for artist in genre
        """
        assert(self.lastfm_artist)

        tags: dict[str, str] = self.lastfm_artist.get("tags", {}).get("tag", [])
        tag_names = [tag["name"] for tag in tags if "name" in tag]
        self.lastfm_tags = tag_names
        return(self.lastfm_tags)

    def attach_artist_lastfm(self) -> LastFmArtist:
        """Attach the lastfm artist to the object, along with additional attributes

        Raises:
            Exception: If search by name or mbid doesn't work

        Returns:
            LastFmArtist: The artist object as returned by lastfm
        """
        baseParams = {
            "method": "artist.getInfo",
            "format": "json"
        }

        lastfm_artist = None
        # Try with musicbrainz id
        try:
            logger.info(f'Searching for lastfm artist by mbid {self.mbid}')
            artist = self.lastfm.get_lastfm_artist_data(baseParams, mbid=self.mbid)
            lastfm_artist = self._attach_lastfm_artist(artist)
            if(lastfm_artist):
                return(lastfm_artist)
            else:
                logger.warning('Artist not found')
        except Exception as e:
            logger.warning(f'Couldn\'t get lastfm artist by mbid {self.mbid}: {e}')

        if(not lastfm_artist):
            # Fallback to artist name
            try:
                logger.info(f'Searching for lastfm artist by name {self.name}')
                artist = self.lastfm.get_lastfm_artist_data(baseParams, name = self.name)
                lastfm_artist = self._attach_lastfm_artist(artist)
                if(lastfm_artist):
                    return(lastfm_artist)
                else:
                    logger.warning('Artist not found')
            except Exception as e:
                logger.warning(f'Couldn\'t get lastfm artist by name {self.name}: {e}')

        raise Exception(f'Couldn\'t get lastfm artist for {self.name}')

    def artist_in_lastfm_genre(self, genre: str) -> bool:
        """Check if the artist lastfm object is in the genre

        Returns:
            bool: Is it?
        """
        if (not hasattr(self, 'lastfm_artist')):
            self.lastfm_artist = self.attach_artist_lastfm()
        return(genre in self._get_tags_from_lastfm_artist())

    def get_artist_top_tracks_lastfm(self, limit: int = 10) -> list[Track]:
        """
        Fetches the top tracks of an artist from Last.fm.

        Args:
            limit (int, optional): Number of top tracks to retrieve. Defaults to 10.

        Returns:
            list[Track]: A list of the top tracks.
        """
        baseParams = {
            'method': 'artist.gettoptracks',
            'format': 'json',
            'limit': limit
        }

        tracks = None
        try:
            logger.info(f'Attaching top tracks from mbid for {self.name}')
            data = self.lastfm.get_lastfm_artist_data(baseParams, mbid = self.mbid)
            tracks = self._attach_top_tracks_lastfm(data)
            if(tracks):
                return(tracks)
            else:
                logger.warning('No tracks found')
        except Exception:
            logger.warning(f'Couldn\'t attach top tracks from mbid for {self.name}')
        
        if(not tracks):
            try:
                logger.info(f'Attaching top tracks from name for {self.name}')
                data = self.lastfm.get_lastfm_artist_data(baseParams, name = self.name)
                tracks = self._attach_top_tracks_lastfm(data)
                if(tracks):
                    return(tracks)
                else:
                    logger.warning('No tracks found')
            except Exception:
                logger.warning(f'Couldn\'t attach top tracks from name for {self.name}')

        raise Exception(f'Couldn\'t get lastfm top tracks for {self.name}')

    def attach_spotify_artist_from_track(self, track: Track) -> SpotifyArtist:
        """Attach a spotify artist object from a Track object

        Args:
            track (Track): Track

        Raises:
            Exception: Track not by artist (name)
            Exception: Track not by artist (spotify ID)
            Exception: Something else

        Returns:
            SpotifyArtist: The artist object, as returned by spotify
        """
        if(getattr(self, 'spotify_artist', None)):
            logger.info(f'Artist {self.name} has associated spotify artist')
            return(self.spotify_artist)

        try:
            if(not strcomp(self.name, track.artist)):
                raise Exception(f'Song {track.name} is by {track.artist}, not {self.name}')
            
            logger.info(f"Searching Spotify for Track: '{track.name}' by Artist: '{track.artist}'")

            spotify_track = track.attach_spotify_track_information()

            # Extract the artist ID from the Spotify track
            for spotify_artist in spotify_track['artists']:
                if(strcomp(spotify_artist['name'], track.artist)):
                    self.spotify_artist_id = spotify_artist['id']
                    break
            
            if((not hasattr(self, 'spotify_artist_id')) or (not track.artist_id_in_spotify_track(self.spotify_artist_id))):
                raise Exception(f'Could not find artist {self.name} ({self.spotify_artist_id}) in track {track.name}')
            
            logger.info(f"Spotify Artist ID: {self.spotify_artist_id}")

            spotify_artist         = self.user.get_spotify_artist_by_id(self.spotify_artist_id)
            self.spotify_artist    = spotify_artist
            self.spotify_followers = int(spotify_artist.get('followers', {}).get('total', 0))

            logger.info(f"Retrieved Spotify Artist: {spotify_artist['name']} (ID: {spotify_artist['id']})")

            return(self.spotify_artist)

        except Exception as e:
            logger.error(e)
            raise Exception(f"Could not attach spotify artist {self.name} from track {track.name}")

