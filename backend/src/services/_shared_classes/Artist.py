import re

from langdetect  import detect

from src.services._shared_classes.Track       import Track
from src.services.genre_handling.valid_genres import genre_is_spotify, convert_genre

from src.utils.musicbrainz_util import MusicBrainzArtist
from src.utils.logger           import logger
from src.utils.util             import strcomp, map_language_codes, filter_low_count_entries
from src.utils.spotify_util     import SpotifyArtist

from src.auth.LastFMRequests import LastFMRequests, LastFmArtist
from src.auth.SpotifyUser    import spotify_user

class Artist:
    """Representing an artist, at a high level

    Attributes:
        name
        mbid
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
    def __init__(self, name: str, mbid: str) -> None:
        """Initialize the artist

        Args:
            name (str): Artist name
            mbid (str): Artist MBID
        """
        self.name   = name
        self.mbid   = mbid
        self.lastfm = LastFMRequests()

    @classmethod
    def from_musicbrainz(cls, musicbrainz_artist_object: MusicBrainzArtist) -> 'Artist':
        """Create artist from musicbrainz artist object

        Args:
            musicbrainz_artist_object (MusicBrainzArtist): Artist object as returned by musicbrainz

        Raises:
            Exception: If the musicbrainz artist is missing name or mbid or user invalid

        Returns:
            Artist: The artist
        """
        try:
            name = musicbrainz_artist_object.get('name', "")
            mbid = musicbrainz_artist_object.get('id', "")
            if (name and mbid):
                artist = cls(name, mbid)
                return(artist)
            else:
                raise Exception('Name or ID doesn\'t exist')
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
                valid_tracks.append(Track.from_lastfm(track))
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

        logger.info(f'Artist {self.name} lastfm tags: {self.lastfm_tags}')

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

    def lastfm_page_is_conglomerate(self) -> bool:
        if (not hasattr(self, 'lastfm_artist')):
            self.lastfm_artist = self.attach_artist_lastfm()

        artist: LastFmArtist = self.lastfm_artist
        
        summary = artist.get('bio', {}).get('summary', '')
        content = artist.get('bio', {}).get('content', '')

        def is_conglomerate_page(input_string):
            """
            Determines if the input string matches a specific pattern indicating that
            a Last.fm page is a conglomerate for many artists.

            The pattern matches phrases starting with "There are" or "There is" followed by expressions like:
            - "at least x" where x can be a digit or a number word (e.g., "five")
            - "multiple"
            - "many"
            - "several"
            - "numerous"
            - "a couple"
            - "a few"

            Then followed by one or more of the words:
            - "bands"
            - "artists"
            - "groups"
            - "singers"
            - "musicians"
            - "duos"

            Optionally followed by "and/or" and another of the specified words, and ending with "named" or "called",
            possibly followed by additional words and optional punctuation.

            Parameters:
            - input_string (str): The string to be checked against the pattern.

            Returns:
            - bool: True if the input string matches the pattern at the start, False otherwise.
            """

            # List of number words
            number_words = [
                'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
                'eighteen', 'nineteen', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
                'eighty', 'ninety', 'hundred', 'thousand', 'million', 'billion', 'trillion'
            ]

            # Join number words into a regex pattern
            number_words_pattern = '|'.join(number_words)

            # Regular expression pattern
            pattern = rf"""
                ^there\s+(?:is|are)\s+                          # Match 'there is' or 'there are' at the start
                (?:
                    (?:at\s+least\s+)?                          # Optional 'at least'
                    (?:\d+|{number_words_pattern})|             # Digits or number words
                    multiple|                                   # or 'multiple'
                    many|                                       # or 'many'
                    several|                                    # or 'several'
                    numerous|                                   # or 'numerous'
                    a\s+couple|                                 # or 'a couple'
                    a\s+few                                     # or 'a few'
                )
                \s+
                (?:bands|artists|groups|singers|musicians|duos)     # One of the specified words
                (?:
                    \s+(?:and|or)\s+                            # 'and' or 'or' with surrounding spaces
                    (?:bands|artists|groups|singers|musicians|duos) # Another specified word
                )?
                \s+
                (?:named|called)                                # 'named' or 'called'
                (?:\s+\S+)*                                     # Optionally, additional words after 'named' or 'called'
                \s*[\.,:]*                                      # Optional trailing punctuation
            """

            # Compile the regex pattern with IGNORECASE and VERBOSE flags
            regex = re.compile(pattern, re.IGNORECASE | re.VERBOSE)

            # Strip leading/trailing whitespace from input string
            input_string = input_string.strip()

            # Attempt to match the pattern at the start of the input string
            match = regex.match(input_string)

            # Return True if a match is found, False otherwise
            return bool(match)
        
        return(is_conglomerate_page(summary) or is_conglomerate_page(content))

    def artist_in_lastfm_genre(self, genre: str) -> bool:
        """Check if the artist lastfm object is in the genre

        Returns:
            bool: Is it?
        """
        if (not hasattr(self, 'lastfm_artist')):
            self.lastfm_artist = self.attach_artist_lastfm()
        
        if (genre_is_spotify(genre)):
            converted_genre = convert_genre('SPOTIFY', 'LASTFM', genre)
        else:
            converted_genre = convert_genre('MUSICBRAINZ', 'LASTFM', genre)

        return (converted_genre in self._get_tags_from_lastfm_artist())

    def get_artist_top_tracks_lastfm(self, limit: int = 5) -> list[Track]:
        """
        Fetches the top tracks of an artist from Last.fm.

        Args:
            limit (int, optional): Number of top tracks to retrieve. Defaults to 5.

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

        logger.error(f'Couldn\'t get lastfm top tracks for {self.name}')
        return([])

    def attach_spotify_artist(self, artist: SpotifyArtist) -> SpotifyArtist:
        """Attach spotify artist to artist from SpotifyArtist object

        Args:
            artist (SpotifyArtist): Artist as returned by spotify (e.g. in /artist/)

        Raises:
            Exception: Not same name
            Exception: Other

        Returns:
            SpotifyArtist: The same as param
        """
        if(getattr(self, 'spotify_artist', None)):
            logger.info(f'Artist {self.name} has associated spotify artist')
            return(self.spotify_artist)

        try:
            name = artist.get('name', '')
            if(not strcomp(self.name, name)):
                raise Exception(f'Artist {name} is not {self.name}')
            
            self.spotify_artist_id = artist.get('id', '')

            logger.info(f"Spotify Artist ID: {self.spotify_artist_id}")

            self.spotify_artist    = artist
            self.spotify_followers = int(artist.get('followers', {}).get('total', 0))

            logger.info(f"Retrieved Spotify Artist: {name} (ID: {artist['id']})")

            return(self.spotify_artist)

        except Exception as e:
            logger.error(e)
            raise Exception(f"Could not attach spotify artist {self.name} from spotify artist id {artist.get('id', '')}")


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
            for spotify_artist in spotify_track.get('artists', []):
                if(strcomp(spotify_artist['name'], track.artist)):
                    self.spotify_artist_id = spotify_artist['id']
                    break
            
            if((not hasattr(self, 'spotify_artist_id')) or (not track.artist_id_in_spotify_track(self.spotify_artist_id))):
                raise Exception(f'Could not find artist {self.name} ({self.spotify_artist_id}) in track {track.name}')
            
            logger.info(f"Spotify Artist ID: {self.spotify_artist_id}")

            spotify_artist         = spotify_user.get_spotify_artist_by_id(self.spotify_artist_id)
            self.spotify_artist    = spotify_artist
            self.spotify_followers = int(spotify_artist.get('followers', {}).get('total', 0))

            logger.info(f"Retrieved Spotify Artist: {spotify_artist['name']} (ID: {spotify_artist['id']})")

            return(self.spotify_artist)

        except Exception as e:
            logger.error(e)
            raise Exception(f"Could not attach spotify artist {self.name} from track {track.name}")
        
    def get_language_guess_spotify(self) -> str:
        assert(hasattr(self, 'spotify_artist'))
        # Only 30% to be considered a language the artist sings in since this fn is prone to error
        pct_min=30

        top_tracks = spotify_user.execute('artist_top_tracks', self.spotify_artist_id)
        track_names = [track.get('name') for track in top_tracks.get('tracks', [])]

        languages = []
        for name in track_names:
            try:
                language = detect(name)
                languages.append(language)
            except Exception:
                continue

        return(filter_low_count_entries(map_language_codes(language_codes=languages, iso639_type=1), pct_min=pct_min))

