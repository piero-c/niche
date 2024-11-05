# Module for finding the niche songs for a genre
from auth.SpotifyUser import SpotifyUser

from services.playlist_maker.PlaylistRequest import PlaylistRequest
from services.playlist_maker.Playlist import NicheTrack
from services.playlist_maker.Artist import Artist
from services._shared_classes.Validator import Validator

from utils.util import load_env, obj_array_to_obj, NICHEMAP, LANGMAP

from db.DB import DB
from db.DAOs.ArtistsDAO import ArtistsDAO
from db.DAOs.RequestsCacheDAO import RequestsCacheDAO
from db.DAOs.RequestsDAO import RequestDAO
from models.pydantic.RequestsCache import ParamsCache, REASONMAP, ReasonExcluded, Excluded
from models.pydantic.Request import Stats

import random
from numpy import mean as mean
from datetime import datetime, timedelta

from utils.logger import logger
env    = load_env()

# TODO-  remove the bidicts? Mongo takes enums as lookups
# TODO - Handle logic related to not having enough songs (api)
# TODO - english name of artist or song like 力那 (li na)
# TODO - Split into validator object

# TODO - Logic for request type - like for stats sake dont count extenders as requests
# TODO - decrease likeness? two cartoons artist slaps

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
    """
    def __init__(self, request: PlaylistRequest, user: SpotifyUser) -> None:
        """Initialize the finder

        Args:
            request (PlaylistRequest): The playlist request
            user (SpotifyUser): Spotify Authenticated User
        """
        self.request   = request
        self.user      = user

        self.validator        = Validator(request, user)
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
                    a = Artist.from_musicbrainz(artist, self.user)
                    if a:
                        artist_list.append(a)
                except Exception as e:
                    logger.error(f"Could not create artist: {e}")
            return(artist_list)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return([])
        
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
    
    def _add_excluded_entry(self, artist: Artist, reason: ReasonExcluded) -> None:
        """_summary_

        Args:
            artist (Artist): _description_
            reason (ReasonExcluded): _description_
        """
        self.requestsCacheDAO.check_and_update_or_add_excluded(
            cache_id=self.requestsCacheOID,
            excluded=self._create_excluded_object(artist, reason)
        )

    def fetch_valid_artists(self, artists: list[Artist]) -> list[Artist]:
        valid_artists: list[Artist] = []
        for artist in artists:
            # Check if artist is invalid in cache
            if (not artist) or (self._artist_cached_invalid(artist)):
                logger.error(f'Artist {artist.name} has been previously cached as invalid for this request')
                continue
            else:
                # Check if artist is excluded
                excluded_reason = self.validator.artist_excluded_reason_lastfm(artist)
                if ((excluded_reason) and (excluded_reason != ReasonExcluded.OTHER)):
                    self._add_excluded_entry(artist, excluded_reason)
                    continue
                # For other, it may be an error or something we dont want to put a excluded entry for
                elif (excluded_reason):
                    continue
                else:
                    valid_artists.append(artist)
        random.shuffle(valid_artists)
        return(valid_artists)

    def find_niche_tracks(self) -> list[NicheTrack]:
        """Make the playlist

        Returns:
            list[NicheTrack]: List of niche tracks
        """
        artists_song_count = {}
        # TODO - make dynamic / selected by user?
        artist_max_songs  = 1
        artists_total_followers = 0

        niche_tracks      = []

        desired_song_count     = self.request.playlist_length
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

            valid_artists = self.fetch_valid_artists(artists)

            for artist in valid_artists:
                if(len(niche_tracks) >= desired_song_count):
                    break

                # Check the artist's top tracks
                top_tracks = self.validator.get_top_tracks(artist)
                for track in top_tracks:
                    # Enough tracks or max tracks for artist
                    if (len(niche_tracks) >= self.request.playlist_length) or (artists_song_count.get(artist.mbid, 0) >= artist_max_songs):
                        logger.warning('Playlist or artist song count reached')
                        break
                    try:
                        # Get the spotify artist from the lastfm top tracks (so that we decrease the chance of getting the wrong artist from name search alone)
                        # Attach the spotify artist from the track and ensure it was attached
                        if (self.validator.attached_spotify_artist_from_track(artist, track)):

                            # Discard artist if excluded by spotify metrics
                            # I know this runs for every track but I attach the artist from the track and I'm not setting globals:)
                            artist_exclusion_spotify = self.validator.check_artist_exclusion_spotify(artist)
                            if ((artist_exclusion_spotify) and (artist_exclusion_spotify != ReasonExcluded.OTHER)):
                                self._add_excluded_entry(artist, artist_exclusion_spotify)
                                break
                            else:
                                # Artist is valid. If it was previously excluded  delete that entry
                                self.requestsCacheDAO.delete_excluded_entry(self.requestsCacheOID, artist.mbid)

                            # Attach the track's spotify information
                            track.attach_spotify_track_information(artist.spotify_artist_id)
                            logger.info(f'Attached spotify track info for {track.name}')
                            
                            # Ensure track length and type valid
                            if (self.validator.validate_track(track)):
                                # Add track to niche_tracks
                                niche_track = {
                                    'artist'     : artist.name,
                                    'track'      : track.name,
                                    'spotify_uri': track.spotify_uri,
                                    'spotify_url': track.spotify_url,
                                }
                                niche_tracks.append(niche_track)

                                artists_song_count[artist.mbid] = artists_song_count.get(artist.mbid, 0) + 1
                                artists_total_followers += artist.spotify_followers
                                percent_artists_valid = (len(niche_tracks) / ((i + 1) * artist_increment_count)) * 100

                                logger.success(f"ADDED NICHE TRACK: {artist.name} - {track.name}")
                                logger.success(f"TRACKS ADDED: {len(niche_tracks)}")
                                logger.success(f"RATIO: {percent_artists_valid}%")

                    except Exception as e:
                        logger.error(f"Error processing tracks for artist {artist.name}: {e}")
                        continue

        # Update the stats of the request
        rdao = RequestDAO(self.db)
        rdao.update(self.request.request_oid, {
            'stats': Stats(
                percent_artists_valid= percent_artists_valid,
                average_artist_followers= (artists_total_followers / len(niche_tracks))
            )
        })


        return(niche_tracks)
            

