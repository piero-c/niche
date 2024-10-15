import requests
from scripts.musicbrainz_util import get_tags_from_musicbrainz_taglist
from scripts.playlist_maker.Track import Track
from scripts.playlist_maker.PlaylistRequest import Language
from scripts.util import sleep, RequestType, strcomp
from scripts.spotify_util import SpotifyArtist
from scripts.lastfm_util import LASTFM_API_KEY, LASTFM_API_URL, LastFmArtist
from scripts.musicbrainz_util import MusicBrainzArtist
import spotipy

class Artist:
    """_summary_
    """
    def __init__(self, name: str, mbid: str) -> None:
        """_summary_

        Args:
            name (str): _description_
            mbid (str): _description_
        """
        self.name             = name
        self.mbid             = mbid
        self.musicbrainz_tags = []
        self.lastfm_tags      = []

    @classmethod
    def from_musicbrainz(cls, musicbrainz_artist_object: MusicBrainzArtist) -> 'Artist':
        """_summary_

        Args:
            musicbrainz_artist_object (MusicBrainzArtist): _description_

        Returns:
            Artist: _description_
        """
        try:
            name = musicbrainz_artist_object.get('name', "")
            mbid = musicbrainz_artist_object.get('id', "")
            artist = cls(name, mbid)
            tags = get_tags_from_musicbrainz_taglist(musicbrainz_artist_object.get('tag-list', []))
            artist.musicbrainz_tags = tags
            return artist
        except:
            raise Exception(f'Could not create artist from musicbrainz for {name}')

    def get_artist_language(musicbrainz_artist_object: MusicBrainzArtist) -> Language:
        """Return the language of the artist.

        Args:
            musicbrainz_artist_object (MusicBrainzArtist): MusicBrainz artist object.

        Returns:
            Language: The artist's language.
        """
        # TODO
        pass

    def _create_genre_list(self) -> list:
        """
        Returns the intersection of all provided lists of tags.

        Returns:
            list: A list containing elements that are present in all input lists.
        """
        assert(hasattr(self, 'lastfm_tags'))
        assert(hasattr(self, 'musicbrainz_tags'))


        # Convert both lists to sets to perform intersection
        lastfm_set = set(self.lastfm_tags)
        musicbrainz_set = set(self.musicbrainz_tags)

        # Find the intersection of both sets
        intersection = lastfm_set & musicbrainz_set

        self.genres = list(intersection)
        # Convert the set back to a list (optional: sort the list if desired)
        return(self.genres)

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
        self._get_tags_from_lastfm_artist()
        return(self.lastfm_artist)

    def _get_lastfm_data(self, type: str, baseParams: dict) -> LastFmArtist:
        """_summary_

        Args:
            type (str): _description_

        Returns:
            LastFmArtist: _description_
        """
        params = baseParams.copy()

        if (type == 'mbid'):
            params["mbid"] = self.mbid
        elif (type == 'name'):
            params["artist"] = self.name

        ## BEGIN REQUEST ##
        response = requests.get(LASTFM_API_URL, params=params)
        sleep(RequestType.LASTFM)
        ## END REQUEST ##
        if (response.status_code == 200):
            api_data = response.json()
        
        return(api_data)


    def attach_artist_lastfm(self) -> LastFmArtist:
        """_summary_

        Raises:
            Exception: _description_

        Returns:
            LastFmArtist: _description_
        """
        baseParams = {
            "method": "artist.getInfo",
            "api_key": LASTFM_API_KEY,
            "format": "json"
        }

        # Try with musicbrainz id
        try:
            print(f'Searching for lastfm artist by mbid {self.mbid}')
            artist = self._get_lastfm_data('mbid', baseParams)
            lastfm_artist = self._attach_lastfm_artist(artist)
            if (lastfm_artist):
                return(lastfm_artist)
            else:
                print('Artist not found')
        except:
            print(f'Couldn\'t get lastfm artist by mbid {self.mbid}')

        # Fallback to artist name
        try:
            print(f'Searching for lastfm artist by name {self.name}')
            artist = self._get_lastfm_data('name', baseParams)
            lastfm_artist = self._attach_lastfm_artist(artist)
            if (lastfm_artist):
                return(lastfm_artist)
            else:
                print('Artist not found')
        except:
            print(f'Couldn\'t get lastfm artist by name {self.name}')

        raise Exception(f'Couldn\'t get lastfm artist for {self.name}')
    
    def artist_in_genre(self, genre: str) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        self.tags = self._create_genre_list()
        if (not genre in self.tags):
            print(f'Artist {self.name} tags {self.tags} invalid.')
            return(False)
        return(True)

    def _attach_top_tracks_lastfm(self, tracks: dict) -> list[Track]:
        tracks = tracks.get('toptracks', {}).get('track', [])
        valid_tracks = []
        for track in tracks:
            try:
                valid_tracks.append(Track.from_lastfm(track))
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
        # TODO - Fall back on artist?? - And encorporate lastfm
        baseParams = {
            'method': 'artist.gettoptracks',
            'api_key': LASTFM_API_KEY,
            'format': 'json',
            'limit': limit
        }

        try:
            print(f'Attaching top tracks from mbid for {self.name}')
            data = self._get_lastfm_data('mbid', baseParams)
            tracks = self._attach_top_tracks_lastfm(data)
            if(tracks):
                return (tracks)
            else:
                print('No tracks found')
        except:
            print(f'Couldn\'t attach top tracks from mbid for {self.name}')
        
        try:
            print(f'Attaching top tracks from name for {self.name}')
            data = self._get_lastfm_data('name', baseParams)
            tracks = self._attach_top_tracks_lastfm(data)
            if(tracks):
                return (tracks)
            else:
                print('No tracks found')
        except:
            print(f'Couldn\'t attach top tracks from name for {self.name}')

        raise Exception(f'Couldn\'t get lastfm top tracks for {self.name}')

    # TODO - Eventually can just get the link from musicbrainz by artist search with ?inc=url-rels 
    def attach_spotify_artist_from_track(self, track: Track, spotipy_methods: spotipy.Spotify) -> SpotifyArtist:
        """_summary_

        Args:
            track (Track): _description_
            spotipy_methods (spotipy.Spotify): _description_

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

            spotify_track = track.attach_spotify_track_information(spotipy_methods)

            # Extract the artist ID from the Spotify track
            for spotify_artist in spotify_track['artists']:
                if (strcomp(spotify_artist['name'], track.artist)):
                    self.spotify_artist_id = spotify_artist['id']
                    break
            
            if (not hasattr(self, 'spotify_artist_id')):
                raise Exception(f'Could not find artist {self.name} in track {track.name}')
            
            print(f"Spotify Artist ID: {self.spotify_artist_id}")

            ## BEGIN REQUEST ##
            # Retrieve the full artist object from Spotify using the artist ID
            spotify_artist = spotipy_methods.artist(self.spotify_artist_id)
            sleep(RequestType.SPOTIFY)
            ## END REQUEST ##

            self.spotify_artist = spotify_artist
            self.spotify_followers = int(spotify_artist.get('followers', {}).get('total', 0))

            print(f"Retrieved Spotify Artist: {spotify_artist['name']} (ID: {spotify_artist['id']})")

            return(self.spotify_artist)

        except Exception as e:
            print(e)
            raise Exception(f"Could not attach spotify artist {self.name} from track {track.name}")

