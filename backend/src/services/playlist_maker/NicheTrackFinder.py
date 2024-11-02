# Module for finding the niche songs for a genre
from auth.SpotifyUser import SpotifyUser
from auth.MusicBrainzRequests import MusicBrainzRequests

from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language
from services.playlist_maker.Playlist import NicheTrack
from services.playlist_maker.Artist import Artist

from utils.util import load_env, obj_array_to_obj, NICHEMAP, LANGMAP

from db.DB import DB
from db.ArtistsDAO import ArtistsDAO
from db.RequestsCacheDAO import RequestsCacheDAO
from models.pydantic.RequestsCache import ParamsCache, REASONMAP, ReasonExcluded, Excluded

import random
from numpy import mean as mean
from datetime import datetime, timedelta

from utils.logger import logger
env    = load_env()

# TODO-  remove the bidicts? Mongo takes enums as lookups
# TODO - go thru check pydocs and simplify all code
# TODO - for some infos (successes, see if can do diff log) and better logging in general
# Change rest of warnings that are err to err

ARTIST_EXCLUDED_EARLIEST_DATE = datetime.today() - timedelta(days=182)

class NicheTrackFinder:
    """Niche Track Finder
        
    Attributes:
        request
        user
        artistsDAO
        requestsCacheDAO
        requestsCacheOID
        requests_cache
        excluded_artists
        artist_excluded_earliest_date
    """
    def __init__(self, request: PlaylistRequest, user: SpotifyUser) -> None:
        """Initialize the finder

        Args:
            request (PlaylistRequest): The playlist request
            user (SpotifyUser): Spotify Authenticated User
        """
        self.request         = request
        self.user            = user

        self.db               = DB()
        self.artistsDAO       = ArtistsDAO(self.db)
        self.requestsCacheDAO = RequestsCacheDAO(self.db)

        self.requests_cache = self.requestsCacheDAO.create_if_not_exists(
            ParamsCache(
                language=LANGMAP.inv.get(self.request.language),
                genre=self.request.genre,
                niche_level=NICHEMAP.inv.get(self.request.niche_level)
            )
        )
        try:
            self.requestsCacheOID = self.requests_cache.inserted_id
            self.requests_cache = self.requestsCacheDAO.read_by_id(self.requestsCacheOID)
        except Exception:
            self.requestsCacheOID = self.requests_cache.id
        
        # Create a lookup for excluded artists so we don't have to query the db
        self.excluded_artists = obj_array_to_obj([excl.model_dump(by_alias=True) for excl in self.requests_cache.excluded], 'mbid')

    def _fetch_artists_from_musicbrainz(self) -> list[Artist]:
        """Get artists from musicbrainz in the requested genre
        """
        try:
            artist_list = []
            artists = self.artistsDAO.get_artists_in_genre(self.request.genre)
            for artist in artists:
                try:
                    artist_list.append(Artist.from_musicbrainz(artist, self.user))
                except Exception as e:
                    logger.error(f"Could not create artist: {e}")
            return(artist_list)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return([])
        
    def _artist_likeness_invalid(self, artist: Artist) -> bool:
        """Valid according to request
        """
        if (artist.lastfm_artist_likeness < self.request.lastfm_likeness_min):
            logger.error(f'Artist likeness ({artist.lastfm_artist_likeness}) invalid')
            return(True)
        
        return(False)

    def _artist_listeners_and_plays_too_low(self, artist: Artist) -> bool:
        """Too low according to request for nicheness level
        """
        listeners = artist.lastfm_artist_listeners
        playcount = artist.lastfm_artist_playcount

        if((listeners < self.request.lastfm_listeners_min) and (playcount < self.request.lastfm_playcount_min)):
            logger.error(f'Artist {artist.name} listeners {listeners} and playcount {playcount} too low')
            return(True)

        return(False)

    def _artist_listeners_and_plays_too_high(self, artist: Artist) -> bool:
        """Too high according to request for nicheness level
        """
        listeners = artist.lastfm_artist_listeners
        playcount = artist.lastfm_artist_playcount

        if((listeners > self.request.lastfm_listeners_max) and (playcount > self.request.lastfm_playcount_max)):
            logger.error(f'Artist {artist.name} listeners {listeners} and playcount {playcount} too high')
            return(True)

        return(False)

    def _artist_cached_invalid(self, artist: Artist) -> bool:
        """Check the previously excluded artists to check if the artist has been previously excluded within the correct timeframe or for the right reason

        Args:
            artist (Artist): The artist to check

        Returns:
            bool: Were they excluded?
        """
        artist_cached_entry = self.excluded_artists.get(artist.mbid, None)

        # If the artist has been cached for this request as invalid 
        #   AND (either they were excluded within the heuristic timeframe (where they would Probably still be excluded if checked again) OR
        #        they were excluded for being too popular OR for not singing in the requested language)
        #   then they are still invalid
        if (
            (artist_cached_entry) and (
                (artist_cached_entry.get('date_excluded') > ARTIST_EXCLUDED_EARLIEST_DATE) or
                (
                    (artist_cached_entry.get('reason_excluded') == REASONMAP.get(ReasonExcluded.TOO_MANY_SOMETHING)) or
                    (artist_cached_entry.get('reason_excluded') == REASONMAP.get(ReasonExcluded.WRONG_LANGUAGE))
                )
            )
        ):
            return(True)
        
        return(False)

    def _create_excluded_object(self, artist: Artist, reason: ReasonExcluded) -> Excluded:
        """Create an Excluded object

        Args:
            artist (Artist): The artist to exclude
            reason (ReasonExcluded): The reason to exclude them

        Returns:
            Excluded: The Excluded object
        """
        return (Excluded(
            name=artist.name,
            mbid=artist.mbid,
            reason_excluded=REASONMAP.get(reason)
        ))

    def find_niche_tracks(self) -> list[NicheTrack]:
        """Make the playlist

        Raises:
            Exception: Not enough songs could be added

        Returns:
            list[NicheTrack]: List of niche tracks
        """
        niche_tracks      = []
        artist_song_count = {}

        # TODO - make dynamic / selected by user?
        artist_max_songs = 1

        desired_song_count   = self.request.playlist_length

        artist_increment_count = 25

        artists_list = self._fetch_artists_from_musicbrainz()
        # Using list comprehension with padding to split into groups of 25
        artists_sublists = [artists_list[i:i+artist_increment_count] if len(artists_list[i:i+artist_increment_count]) == artist_increment_count else artists_list[i:i+artist_increment_count] + [None]*(artist_increment_count - len(artists_list[i:i+artist_increment_count])) for i in range(0, len(artists_list), artist_increment_count)]

        # Generate random offsets of artists to search
        offsets_list = list(range(0, len(artists_sublists)))
        random.shuffle(offsets_list)

        for i in range(len(offsets_list)):
            if(len(niche_tracks) >= desired_song_count):
                break
            logger.info(f'artists checked: {i * artist_increment_count}')

            random_offset = offsets_list[i]
            artists: list[Artist] = artists_sublists[random_offset]

            logger.info(f'Checking offset {random_offset} of {len(offsets_list)}')

            valid_artists: list[Artist] = []
            for artist in artists:
                # Check if artist is invalid in cache
                if self._artist_cached_invalid(artist):
                    logger.error(f'Artist {artist.name} has been previously cached as invalid for this request')
                    continue

                try:
                    # Attach artist from lastfm
                    artist.attach_artist_lastfm()
                    logger.info(f'Attached lastfm artist {artist.name} from lastfm')

                    # TODO - here - put the debug log in the functions 
                    # Check artist listener and play thresholds
                    if (self._artist_listeners_and_plays_too_high(artist)):
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.TOO_MANY_SOMETHING)
                        )
                    elif (self._artist_listeners_and_plays_too_low(artist)):
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.TOO_FEW_SOMETHING)
                        )
                    elif (self._artist_likeness_invalid(artist)):
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.NOT_LIKED_ENOUGH)
                        )
                    elif (not artist.artist_in_lastfm_genre(self.request.genre)):
                        # Sanity check for artist match, no exclusion required here
                        pass
                    else:
                        logger.info(f'Artist {artist.name} is valid')
                        # Artist passes all checks
                        valid_artists.append(artist)
                except Exception as e:
                    logger.error(e)


            # Shuffle artists
            random.shuffle(valid_artists)

            for artist in valid_artists:
                if(len(niche_tracks) >= desired_song_count):
                    break

                top_tracks = None
                try:
                    # Get artist's top tracks from lastfm
                    top_tracks = artist.get_artist_top_tracks_lastfm()
                except Exception as e:
                    logger.error(e)
                    continue
                if(not top_tracks):
                    logger.warning(f"No top tracks found on lastfm for artist: {artist.name}")
                    continue

                # Shuffle tracks to add randomness
                random.shuffle(top_tracks)

                attached = False
                # Get the spotify artist from the lastfm top tracks (so that we decrease the chance of getting the wrong artist from name search alone)
                for top_track in top_tracks:
                    try:
                        artist.attach_spotify_artist_from_track(top_track)
                        logger.info(f'Attached spotify artist {artist.name} from lastfm top track')
                        attached = True
                        break
                    except Exception as e:
                        logger.error(e)
                        break

                if(not attached):
                    break

                for track in top_tracks:
                    if((len(niche_tracks) >= desired_song_count) or (artist_song_count.get(artist.mbid, 0) >= artist_max_songs)):
                        logger.warning('song count has been reached OR Artist has hit song count')
                        break
                    if(artist.spotify_followers > self.request.spotify_followers_max):
                        logger.error(f'Artist {artist.name} followers ({artist.spotify_followers}) too high')
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.TOO_MANY_SOMETHING)
                        )
                        break
                    if(artist.spotify_followers < self.request.spotify_followers_min):
                        logger.error(f'Artist {artist.name} followers ({artist.spotify_followers}) too low')
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.TOO_FEW_SOMETHING)
                        )
                        break

                    
                    try:
                        track.attach_spotify_track_information()
                        logger.info(f'Attached spotify track info for {track.name}')
                    except Exception as e:
                        logger.error(e)
                        continue

                    # CHECK DURATION
                    if((track.track_length_seconds < self.request.songs_length_min_secs) or (track.track_length_seconds > self.request.songs_length_max_secs)):
                        logger.warning(f"Skipping track '{track.name}' by '{artist.name}' due to song length constraints.")
                        continue

                    mb = MusicBrainzRequests()
                    # CHECK ARTIST LANGUAGE
                    if((not self.request.language == Language.ANY) and (self.request.language not in mb.get_artist_languages(artist.mbid))):
                        logger.error(f"Artist does not sing in {self.request.language}")
                        self.requestsCacheDAO.check_and_update_or_add_excluded(
                            cache_id=self.requestsCacheOID,
                            excluded=self._create_excluded_object(artist, ReasonExcluded.WRONG_LANGUAGE)
                        )
                        break

                    # TODO
                    # # CHECK YEAR PUBLISHED
                    # if(year_published < self.request.songs_min_year_created):
                    #     logger.warning(f"Skipping track '{track.name}' by '{artist.name}' due to year published constraints.")
                    #     continue

                    # Artist is valid. If it was previously excluded  delete that entry
                    self.requestsCacheDAO.delete_excluded_entry(self.requestsCacheOID, artist.mbid)

                    # TODO want the API to basically return the playlist link and have the web playback sdk show it and then option to save which will b another endpoint
                    #  TODO -  make the playlist public then if they wanna keep it post a thing to api to change it to private (public so can see on sdk web play) and if dont wanna keep it delete it
                    # Add track to niche_tracks
                    niche_track = {
                        'artist'     : artist.name,
                        'track'      : track.name,
                        'spotify_uri': track.spotify_uri,
                        'spotify_url': track.spotify_url,
                    }
                    niche_tracks.append(niche_track)
                    artist_song_count[artist.mbid] = artist_song_count.get(artist.mbid, 0) + 1
                    logger.info(f"ADDED NICHE TRACK: {artist.name} - {track.name}")
                    logger.info(f"TRACKS ADDED: {len(niche_tracks)}")
                    logger.info(f"RATIO: {(len(niche_tracks) / ((i + 1) * artist_increment_count)) * 100}%")


        if(len(niche_tracks) >= desired_song_count):
            return(niche_tracks)
        else:
            raise Exception('Couldn\'t find enough songs')

