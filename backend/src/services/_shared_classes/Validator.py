from enum   import Enum
from bidict import bidict
from numpy  import mean as mean

from src.auth.MusicBrainzRequests import MusicBrainzRequests

from src.services._shared_classes.PlaylistRequest import PlaylistRequest, Language
from src.services._shared_classes.Artist          import Artist
from src.services._shared_classes.Track           import Track
from src.services.genre_handling.valid_genres     import convert_genre

from src.utils.logger import logger

ReasonExcluded = Enum('ReasonExcluded', ['TOO_MANY_SOMETHING', 'NOT_LIKED_ENOUGH', 'WRONG_LANGUAGE', 'TOO_FEW_SOMETHING', 'OTHER'] )
REASONMAP: bidict = bidict({
    ReasonExcluded.TOO_MANY_SOMETHING: "Too Many Followers / Listeners / Plays",
    ReasonExcluded.NOT_LIKED_ENOUGH  : "Ratio of Listeners to Plays Too Small",
    ReasonExcluded.WRONG_LANGUAGE    : "Artist Does Not Sing in the Requested Language",
    ReasonExcluded.TOO_FEW_SOMETHING : "Too Few Followers / Listeners / Plays"
})

# Validator suited for main generation function only. Wrappers for adding songs to the playlist from spotify recommendations or an existing artist can be found in playlist_editor

class Validator:
    """Class for validating tracks and artists

    Properties:
        request
    """

    def __init__(self, request: PlaylistRequest) -> None:
        """ Initialize

        Args:
            request (PlaylistRequest): Request to validate against
        """
        self.request = request

    def artist_likeness_invalid(self, artist: Artist) -> bool:
        """Valid according to request
        Requires:
            Artist has associated lastfm artist
        """
        return(artist.lastfm_artist_likeness < self.request.lastfm_likeness_min)

    def artist_listeners_and_plays_too_low(self, artist: Artist) -> bool:
        """Too low according to request for nicheness level
        Requires:
            Artist has associated lastfm artist
        """
        return((artist.lastfm_artist_listeners < self.request.lastfm_listeners_min) and (artist.lastfm_artist_playcount < self.request.lastfm_playcount_min))

    def artist_listeners_and_plays_too_high(self, artist: Artist) -> bool:
        """Too high according to request for nicheness level
        Requires:
            Artist has associated lastfm artist
        """
        return((artist.lastfm_artist_listeners > self.request.lastfm_listeners_max) and (artist.lastfm_artist_playcount > self.request.lastfm_playcount_max))

    def artist_excluded_reason_spotify(self, artist: Artist) -> ReasonExcluded | None:
        """If there is one, get the reason the artist is excluded based on spotify stats

        Args:
            artist (Artist): The artist
        
        Requires:
            Artist has associated spotify artist

        Returns:
            ReasonExcluded | None: Reason excluded if it exists
        """
        mb = MusicBrainzRequests()
        if(artist.spotify_followers > self.request.spotify_followers_max):
            logger.error(f'Artist {artist.name} followers ({artist.spotify_followers}) too high')
            return(ReasonExcluded.TOO_MANY_SOMETHING)
        if(artist.spotify_followers < self.request.spotify_followers_min):
            logger.error(f'Artist {artist.name} followers ({artist.spotify_followers}) too low')
            return(ReasonExcluded.TOO_FEW_SOMETHING)
        # CHECK ARTIST LANGUAGE
        if((self.request.language != Language.ANY) and (self.request.language not in mb.get_artist_languages(artist.mbid))):
            logger.error(f"Artist does not sing in {self.request.language}")
            return(ReasonExcluded.WRONG_LANGUAGE)
        return(None)

    def validate_track(self, track: Track) -> bool:
        """Is da track valid

        Requires:
            Track has spotify information attached
        """
        if (not track.is_original_with_lyrics()):
            logger.warning(f'Track {track.name} is a cover, instrumental, or special version of a song')
            return(False)

        # CHECK DURATION
        if((track.track_length_seconds < self.request.songs_length_min_secs) or (track.track_length_seconds > self.request.songs_length_max_secs)):
            logger.warning(f"Skipping track '{track.name}' due to song length constraints.")
            return(False)
        
        # TODO
        # # CHECK YEAR PUBLISHED
        # if(year_published < self.request.songs_min_year_created):
        #     logger.warning(f"Skipping track '{track.name}' by '{artist.name}' due to year published constraints.")
        #     continue
        return(True)

    def artist_excluded_reason_lastfm(self, artist: Artist) -> ReasonExcluded | None:
        """If there is one, get the reason the artist is excluded based on lastfm stats

        Args:
            artist (Artist): The artist
        
        Requires:
            Artist has associated lastfm artist

        Returns:
            ReasonExcluded | None: Reason excluded if it exists
        """
        try:
            # Attach artist from lastfm
            artist.attach_artist_lastfm()
            logger.info(f'Attached lastfm artist {artist.name} from lastfm')

            # Check artist listener and play and likeness thresholds
            if (self.artist_listeners_and_plays_too_high(artist)):
                logger.error(f'Artist {artist.name} listeners {artist.lastfm_artist_listeners} and playcount {artist.lastfm_artist_playcount} too high')
                return(ReasonExcluded.TOO_MANY_SOMETHING)

            elif (self.artist_listeners_and_plays_too_low(artist)):
                logger.error(f'Artist {artist.name} listeners {artist.lastfm_artist_listeners} and playcount {artist.lastfm_artist_playcount} too low')
                return(ReasonExcluded.TOO_FEW_SOMETHING)

            elif (self.artist_likeness_invalid(artist)):
                logger.error(f'Artist likeness ({artist.lastfm_artist_likeness}) invalid')
                return(ReasonExcluded.NOT_LIKED_ENOUGH)

            elif (not artist.artist_in_lastfm_genre(convert_genre('SPOTIFY', 'LASTFM', self.request.genre))):
                logger.error(f'Artist {artist.name} not in genre {convert_genre('SPOTIFY', 'LASTFM', self.request.genre)}')
                return(ReasonExcluded.OTHER)

            else:
                logger.info(f'Artist {artist.name} is valid')
                # Artist passes all checks
                return(None)

        except Exception as e:
            logger.error(e)
            return(ReasonExcluded.OTHER)

    def attached_spotify_artist_from_track(self, artist: Artist, track: Track) -> bool:
        """Attach the spotify artist to the artist from the track

        Args:
            artist (Artist): Artist
            track (Track): Track

        Returns:
            bool: Was it attached
        """
        try:
            artist.attach_spotify_artist_from_track(track)
            logger.info(f'Attached Spotify artist {artist.name} from Last.fm top track')
            return(True)
        except Exception as e:
            logger.error(e)
            return(False)

