# Module for finding the niche songs for a genre
from auth.SpotifyUser import SpotifyUser
from auth.MusicBrainzRequests import MusicBrainzRequests

from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language
from services.playlist_maker.Artist import Artist
from services.playlist_maker.Track import Track


from models.pydantic.RequestsCache import ReasonExcluded

from numpy import mean as mean

from utils.logger import logger

# TODO - requires call to... here and in niche track finder

class Validator:
    """_summary_

    Args:

    """

    def __init__(self, request: PlaylistRequest, user: SpotifyUser) -> None:
        """_summary_

        Args:
            request (PlaylistRequest): _description_
            user (SpotifyUser): _description_
        """
        self.request = request
        self.user    = user

    def artist_likeness_invalid(self, artist: Artist) -> bool:
        """Valid according to request
        """
        return(artist.lastfm_artist_likeness < self.request.lastfm_likeness_min)

    def artist_listeners_and_plays_too_low(self, artist: Artist) -> bool:
        """Too low according to request for nicheness level
        """
        return((artist.lastfm_artist_listeners < self.request.lastfm_listeners_min) and (artist.lastfm_artist_playcount < self.request.lastfm_playcount_min))

    def artist_listeners_and_plays_too_high(self, artist: Artist) -> bool:
        """Too high according to request for nicheness level
        """

        return((artist.lastfm_artist_listeners > self.request.lastfm_listeners_max) and (artist.lastfm_artist_playcount > self.request.lastfm_playcount_max))

    # TODO - pydocs 4 these
    def track_artist_excluded_reason(self, artist: Artist) -> ReasonExcluded | None:
        """_summary_

        Args:
            artist (Artist): _description_

        Returns:
            ReasonExcluded | None: _description_
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
        """_summary_

        Args:
            track (Track): _description_

        Returns:
            bool: _description_
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

    # TODO - change name of this and track artist excl
    def artist_excluded_reason_lastfm(self, artist: Artist) -> ReasonExcluded | None:
        """_summary_

        Args:
            artist (Artist): _description_

        Returns:
            ReasonExcluded | None: _description_
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

            # TODO - Deal with this - was excluding alot of artists (make sure we dont run into the issue of getting an artist not in the genre (remember the one the i pray girl fuzzy search thing)) 
            # TODO - maybe remove this but make sure we dont run into the wrong artist thing
            # TODO - for classic rock was not including alot that were actually in the genre (like 'hard rock' but for k-pop not soooo)
            elif (not artist.artist_in_lastfm_genre(self.request.genre)):
                logger.error(f'Artist {artist.name} not in genre {self.request.genre}')
                return(ReasonExcluded.OTHER)
                # Sanity check for artist match, no exclusion required here

            else:
                logger.info(f'Artist {artist.name} is valid')
                # Artist passes all checks
                return(None)

        except Exception as e:
            logger.error(e)
            return(ReasonExcluded.OTHER)

    def check_artist_exclusion_spotify(self, artist: Artist) -> ReasonExcluded | None:
        """_summary_

        Args:
            artist (Artist): _description_

        Returns:
            ReasonExcluded | None: _description_
        """
        # Requires call to attached_artist_spotify first
        artist_excluded_reason = self.track_artist_excluded_reason(artist)
        if (artist_excluded_reason):
            return (artist_excluded_reason)
        return (None)

    def attached_spotify_artist_from_track(self, artist: Artist, track: Track) -> bool:
        """_summary_

        Args:
            artist (Artist): _description_
            track (Track): _description_

        Returns:
            bool: _description_
        """
        try:
            artist.attach_spotify_artist_from_track(track)
            logger.info(f'Attached Spotify artist {artist.name} from Last.fm top track')
            return(True)
        except Exception as e:
            logger.error(e)
            return(False)

    def get_top_tracks(self, artist: Artist) -> list[Track]:
        """_summary_

        Args:
            artist (Artist): _description_

        Returns:
            list[Track]: _description_
        """
        try:
            # Get artist's top tracks from lastfm
            top_tracks = artist.get_artist_top_tracks_lastfm()
            return(top_tracks)
        except Exception as e:
            logger.error(f"Error processing tracks for artist {artist.name}: {e}")
            return([])
