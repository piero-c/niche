from scripts.playlist_maker.Track import Track
from scripts.utils.util import strcomp
from scripts.utils.spotify_util import SpotifyArtist
from scripts.auth_objects.LastFMRequests import LastFmArtist, LastFMRequests
from scripts.auth_objects.SpotifyUser import SpotifyUser
from scripts.utils.musicbrainz_util import MusicBrainzArtist

class Artist:
    """_summary_
    """
    def __init__(self, name: str, mbid: str, user: SpotifyUser) -> None:
        """_summary_

        Args:
            name (str): _description_
            mbid (str): _description_
        """
        self.name             = name
        self.mbid             = mbid
        self.user             = user
        self.lastfm           = LastFMRequests()

    @classmethod
    def from_musicbrainz(cls, musicbrainz_artist_object: MusicBrainzArtist, user: SpotifyUser) -> 'Artist':
        """_summary_

        Args:
            musicbrainz_artist_object (MusicBrainzArtist): _description_

        Raises:
            Exception: _description_

        Returns:
            Artist: _description_
        """
        try:
            name = musicbrainz_artist_object.get('name', "")
            mbid = musicbrainz_artist_object.get('id', "")
            artist = cls(name, mbid, user)
            return artist
        except Exception as e:
            raise Exception(f'Could not create artist from musicbrainz for {name}: {e}')

    def _get_tags_from_lastfm_artist(self) -> list[str]:
        """From an artist, get the lastfm tags.

        Returns:
            list[str]: list of tags.
        """
        assert(self.lastfm_artist)

        tags: dict[str, str] = self.lastfm_artist.get("tags", {}).get("tag", [])
        tag_names = [tag["name"] for tag in tags if "name" in tag]
        self.lastfm_tags = tag_names
        return(self.lastfm_tags)

    def _attach_lastfm_artist(self, artist: LastFmArtist) -> LastFmArtist:
        """_summary_

        Args:
            artist (LastFmArtist): _description_

        Returns:
            LastFmArtist: _description_
        """
        self.lastfm_artist           = artist.get('artist', None)
        self.lastfm_artist_playcount = int(self.lastfm_artist.get('stats', {}).get('playcount', 0))
        self.lastfm_artist_listeners = int(self.lastfm_artist.get('stats', {}).get('listeners', 0))
        self.lastfm_artist_likeness  = self.lastfm_artist_playcount / self.lastfm_artist_listeners if self.lastfm_artist_listeners else 0
        return(self.lastfm_artist)

    def _attach_top_tracks_lastfm(self, tracks: dict) -> list[Track]:
        tracks = tracks.get('toptracks', {}).get('track', [])
        valid_tracks = []
        for track in tracks:
            try:
                valid_tracks.append(Track.from_lastfm(track, self.user))
            except Exception as e:
                print(e)
        
        self.lastfm_tracks = valid_tracks

        return(valid_tracks)

    def attach_artist_top_tracks_lastfm(self, limit: int = 10) -> list[Track]:
        """
        Fetches the top tracks of an artist from Last.fm.

        Args:
            limit (int, optional): Number of top tracks to retrieve. Defaults to 10.

        Returns:
            list[dict]: A list of the top tracks.
        """
        baseParams = {
            'method': 'artist.gettoptracks',
            'format': 'json',
            'limit': limit
        }

        tracks = None
        try:
            print(f'Attaching top tracks from mbid for {self.name}')
            data = self.lastfm.get_lastfm_data('mbid', self.mbid, baseParams)
            tracks = self._attach_top_tracks_lastfm(data)
            if(tracks):
                return (tracks)
            else:
                print('No tracks found')
        except Exception:
            print(f'Couldn\'t attach top tracks from mbid for {self.name}')
        
        if (not tracks):
            try:
                print(f'Attaching top tracks from name for {self.name}')
                data = self.lastfm.get_lastfm_data('name', self.name, baseParams)
                tracks = self._attach_top_tracks_lastfm(data)
                if(tracks):
                    return (tracks)
                else:
                    print('No tracks found')
            except Exception:
                print(f'Couldn\'t attach top tracks from name for {self.name}')

        raise Exception(f'Couldn\'t get lastfm top tracks for {self.name}')

    def attach_artist_lastfm(self) -> LastFmArtist:
        """_summary_

        Raises:
            Exception: _description_

        Returns:
            LastFmArtist: _description_
        """
        baseParams = {
            "method": "artist.getInfo",
            "format": "json"
        }

        lastfm_artist = None
        # Try with musicbrainz id
        try:
            print(f'Searching for lastfm artist by mbid {self.mbid}')
            artist = self.lastfm.get_lastfm_data('mbid', self.mbid, baseParams)
            lastfm_artist = self._attach_lastfm_artist(artist)
            if (lastfm_artist):
                return(lastfm_artist)
            else:
                print('Artist not found')
        except Exception:
            print(f'Couldn\'t get lastfm artist by mbid {self.mbid}')

        if (not lastfm_artist):
            # Fallback to artist name
            try:
                print(f'Searching for lastfm artist by name {self.name}')
                artist = self.lastfm.get_lastfm_data('name', self.name, baseParams)
                lastfm_artist = self._attach_lastfm_artist(artist)
                if (lastfm_artist):
                    return(lastfm_artist)
                else:
                    print('Artist not found')
            except Exception:
                print(f'Couldn\'t get lastfm artist by name {self.name}')

        raise Exception(f'Couldn\'t get lastfm artist for {self.name}')

    def artist_in_lastfm_genre(self, genre: str) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        if (not hasattr(self, 'lastfm_artist')):
            self.lastfm_artist = self.attach_artist_lastfm()
        return(genre in self._get_tags_from_lastfm_artist())

    def attach_spotify_artist_from_track(self, track: Track) -> SpotifyArtist:
        """_summary_

        Args:
            track (Track): _description_

        Raises:
            Exception: _description_
            Exception: _description_
            Exception: _description_

        Returns:
            SpotifyArtist: _description_
        """
        if(getattr(self, 'spotify_artist', None)):
            print(f'Artist {self.name} has associated spotify artist')
            return(self.spotify_artist)

        try:
            if(not strcomp(self.name, track.artist)):
                raise Exception(f'Song {track.name} is by {track.artist}, not {self.name}')
            
            print(f"Searching Spotify for Track: '{track.name}' by Artist: '{track.artist}'")

            spotify_track = track.attach_spotify_track_information()

            # Extract the artist ID from the Spotify track
            for spotify_artist in spotify_track['artists']:
                if (strcomp(spotify_artist['name'], track.artist)):
                    self.spotify_artist_id = spotify_artist['id']
                    break
            
            if ((not hasattr(self, 'spotify_artist_id')) or (not track.artist_id_in_spotify_track(self.spotify_artist_id))):
                raise Exception(f'Could not find artist {self.name} ({self.spotify_artist_id}) in track {track.name}')
            
            print(f"Spotify Artist ID: {self.spotify_artist_id}")

            spotify_artist = self.user.get_spotify_artist_by_id(self.spotify_artist_id)

            self.spotify_artist = spotify_artist
            self.spotify_followers = int(spotify_artist.get('followers', {}).get('total', 0))

            print(f"Retrieved Spotify Artist: {spotify_artist['name']} (ID: {spotify_artist['id']})")

            return(self.spotify_artist)

        except Exception as e:
            print(e)
            raise Exception(f"Could not attach spotify artist {self.name} from track {track.name}")

