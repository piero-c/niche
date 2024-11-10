import random

from numpy    import mean as mean
from numpy    import ceil
from datetime import datetime, timedelta

from src.services._shared_classes.PlaylistRequest          import PlaylistRequest
from src.services._shared_classes.Playlist                 import Playlist
from src.services._shared_classes.Artist                   import Artist
from src.services._shared_classes.Validator                import Validator, REASONMAP, ReasonExcluded
from src.services.playlist_editor.spotify_recs             import get_recommendations
from src.services.genre_handling.valid_genres              import genre_is_spotify
from src.services.playlist_maker.utils.artists_count_check import average_valid_artists_pct

from src.utils.util         import load_env, obj_array_to_obj, NICHEMAP, LANGMAP, MIN_SONGS_FOR_PLAYLIST_GEN
from src.utils.spotify_util import NicheTrack, convert_spotify_track_to_niche_track
from src.utils.logger       import logger

from src.auth.SpotifyUser import spotify_user

from src.db.DB                         import DB
from src.db.DAOs.ArtistsDAO            import ArtistsDAO
from src.db.DAOs.RequestsCacheDAO      import RequestsCacheDAO
from src.models.pydantic.RequestsCache import ParamsCache, Excluded

env    = load_env()

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
    def __init__(self, request: PlaylistRequest) -> None:
        """Initialize the finder

        Args:
            request (PlaylistRequest): The playlist request
        """
        self.request   = request

        db                    = DB()

        self.validator        = Validator(request)
        # NTF Can own its own requests cache dao
        self.requestsCacheDAO = RequestsCacheDAO(db)

        # Create an entry in requests cache for params if it doesnt exist
        self.requests_cache = self.requestsCacheDAO.create_if_not_exists(
            ParamsCache(
                language    = LANGMAP.inv.get(self.request.language),
                genre       = self.request.genre,
                niche_level = NICHEMAP.inv.get(self.request.niche_level)
            )
        )
        # Get the id of the entry and a reference of the entry
        try:
            self.requestsCacheOID = self.requests_cache.inserted_id
            self.requests_cache = self.requestsCacheDAO.read_by_id(self.requestsCacheOID)
        except Exception:
            self.requestsCacheOID = self.requests_cache.id
        
        # Create a lookup for excluded artists so we don't have to query the db
        self.excluded_artists = obj_array_to_obj([excl.model_dump(by_alias=True) for excl in self.requests_cache.excluded], 'mbid')

    def _fetch_artists_from_musicbrainz(self) -> list[Artist]:
        """Get artists from musicbrainz in the requested genre"""
        try:
            artist_list = []
            db                    = DB()
            artistsDAO            = ArtistsDAO(db)
            artists = artistsDAO.get_artists_in_genre(self.request.genre)
            
            for artist in artists:
                try:
                    a = Artist.from_musicbrainz(artist)
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
        """Add an entry in requests cache for the artist

        Args:
            artist (Artist): The artist
            reason (ReasonExcluded): Reason excluded
        """
        self.requestsCacheDAO.check_and_update_or_add_excluded(
            cache_id=self.requestsCacheOID,
            excluded=self._create_excluded_object(artist, reason)
        )

    def _add_from_recs(self, curr_tracks: list[NicheTrack], num_tracks: int) -> bool:
        """Fill the playlist up with spotify recs"""
        FETCH_SIZES  = 6
        max_attempts = 15
        min_size     = self.request.playlist_min_length - len(curr_tracks)
        max_size     = num_tracks
        added        = []
        added_num    = 0

        if (max_size - min_size < 1):
            return(True)

        # Create playlist object to facilitate recommendations
        pl = Playlist(curr_tracks, self.request)

        attempt = 1
        # Get recommendations (valid ones that can be added to the playlist right away)
        # Add them to the list, as well as the playlist to be considered for random artist seed
        # max 10 attempts
        while added_num < max_size and attempt <= max_attempts:
            recs = get_recommendations(pl.url, min(FETCH_SIZES, max_size - added_num))
            for track in recs:
                if(added_num >= max_size):
                    break
                niche_track: NicheTrack = convert_spotify_track_to_niche_track(track)

                artist           = spotify_user.execute('artist', niche_track.get('artist_spotify_id', None))
                artist_followers = artist.get('followers', {}).get('total', 0)

                logger.success(f'Adding track {niche_track.get('track', '')} by {niche_track.get('artist', '')} from spotify recommendations')

                self.request.update_stats(new_track_artist_followers=artist_followers, previous_num_tracks=len(curr_tracks) + len(added))
                added.append(niche_track)
                added_num += 1
                pl.add_track(niche_track)

            attempt += 1

        # Delete all traces of playlist created to interface with get_recommendations
        pl.delete()

        if(added_num < min_size):
            return(False)
        else:
            # Add the songs to the current tracks
            curr_tracks.extend(added)
            return(True)

    def fetch_valid_artists(self, artists: list[Artist]) -> list[Artist]:
        """From the list of artists, return the valid ones for the request

        Args:
            artists (list[Artist]): The list

        Returns:
            list[Artist]: The valid list
        """
        valid_artists: list[Artist] = []
        for artist in artists:
            # Check if artist is invalid in cache
            if (not artist):
                continue
            elif (self._artist_cached_invalid(artist)):
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
        artist_max_songs = 1

        # TODO - explain - here - do expls and docs for scripts then merge branch and onto middlewares / frontend / frontend learning
        desired_valid_artists_multiple_of_min_len = 5

        percent_artists_valid = 0

        niche_tracks = []

        # TODO - change up the sstuff make easier to understand spotify vs mb genre (i.e. like having a spotify seed genre vs mb) idk how but do itlllll

        artist_increment_count = 25

        artists_list = self._fetch_artists_from_musicbrainz()

        # TODO - explain
        if (not genre_is_spotify(self.request.genre)):
            desired_song_count_from_mb_artists = self.request.playlist_min_length
        else:
            previous_valid_pcts = average_valid_artists_pct(self.request)
            if (previous_valid_pcts < 0):
                valid_pct_av = 2
            else:
                valid_pct_av = previous_valid_pcts
            
            expected_num_artists_valid = len(artists_list) * (valid_pct_av/100)
            # 100 - dsc = 20, sc = 1
            # 50  - dsc = 10, sc = .5
            # 25  - dsc = 5, sc = .25
            # TODO - explain
            min_valid_for_max_on_min_pl_len = self.request.playlist_min_length * desired_valid_artists_multiple_of_min_len
            rep_song_scalar = min(1, expected_num_artists_valid / min_valid_for_max_on_min_pl_len)
            desired_song_count_from_mb_artists = max(int(ceil(self.request.playlist_min_length * rep_song_scalar) + 0.00001), MIN_SONGS_FOR_PLAYLIST_GEN)


        # Using list comprehension with padding to split into groups of 25
        artists_sublists = [artists_list[i:i+artist_increment_count] if len(artists_list[i:i+artist_increment_count]) == artist_increment_count else artists_list[i:i+artist_increment_count] + [None]*(artist_increment_count - len(artists_list[i:i+artist_increment_count])) for i in range(0, len(artists_list), artist_increment_count)]
        # Generate random offsets of artists to search
        offsets_list = list(range(0, len(artists_sublists)))
        random.shuffle(offsets_list)

        for i in range(len(offsets_list)):
            if(len(niche_tracks) >= desired_song_count_from_mb_artists):
                break

            logger.info(f'artists checked: {i * artist_increment_count}')

            # Get random subset of artists
            random_offset = offsets_list[i]
            artists: list[Artist] = artists_sublists[random_offset]

            logger.info(f'Checking offset {random_offset} of {len(offsets_list)}')

            valid_artists = self.fetch_valid_artists(artists)

            for artist in valid_artists:
                if(len(niche_tracks) >= desired_song_count_from_mb_artists):
                    break

                # Check the artist's top tracks
                top_tracks = artist.get_artist_top_tracks_lastfm()
                for track in top_tracks:
                    # Enough tracks or max tracks for artist
                    if (len(niche_tracks) >= self.request.playlist_min_length) or (artists_song_count.get(artist.mbid, 0) >= artist_max_songs):
                        logger.warning('Playlist or artist song count reached')
                        break
                    try:
                        # Get the spotify artist from the lastfm top tracks (so that we decrease the chance of getting the wrong artist from name search alone)
                        # Attach the spotify artist from the track and ensure it was attached
                        if (self.validator.attached_spotify_artist_from_track(artist, track)):
                            # Discard artist if excluded by spotify metrics
                            # I know this runs for every track but I attach the artist from the track and I'm not setting globals:)
                            artist_exclusion_spotify = self.validator.artist_excluded_reason_spotify(artist)
                            artist_exclusion_language = self.validator.artist_excluded_language(artist)
                            if ((artist_exclusion_spotify) and (artist_exclusion_spotify != ReasonExcluded.OTHER)):
                                self._add_excluded_entry(artist, artist_exclusion_spotify)
                                break
                            elif (artist_exclusion_language):
                                self._add_excluded_entry(artist, artist_exclusion_language)
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
                                niche_track: NicheTrack = {
                                    'artist'             : artist.name,
                                    'artist_spotify_id'  : artist.spotify_artist_id,
                                    'track'              : track.name,
                                    'spotify_uri'        : track.spotify_uri,
                                    'spotify_url'        : track.spotify_url,
                                }
                                niche_tracks.append(niche_track)

                                # Update variables related to the generation
                                artists_song_count[artist.mbid] = artists_song_count.get(artist.mbid, 0) + 1
                                artist_followers = artist.spotify_followers
                                percent_artists_valid = (len(niche_tracks) / ((i + 1) * artist_increment_count)) * 100

                                # Update the stats of the request
                                self.request.update_stats(new_track_artist_followers=artist_followers, previous_num_tracks=len(niche_tracks)-1)

                                logger.success(f"ADDED NICHE TRACK: {artist.name} - {track.name}")
                                logger.success(f"TRACKS ADDED: {len(niche_tracks)}")
                                logger.success(f"RATIO: {percent_artists_valid}%")

                    except Exception as e:
                        logger.error(f"Error processing tracks for artist {artist.name}: {e}")
                        continue

        # Update the valid percent stat of the request
        self.request.update_stats(percent_artists_valid_new_val=percent_artists_valid)

        # If not enough songs to extend playlist raise an error, else try to extend the playlist. If that doesnt work, throw an error
        if (len(niche_tracks) < MIN_SONGS_FOR_PLAYLIST_GEN):
            raise Exception("Not enough songs")
        else:
            logger.info(f'Playlist length {len(niche_tracks)}, fetching from spotify recommendations')
            if(not self._add_from_recs(niche_tracks, self.request.playlist_max_length - len(niche_tracks))):
                raise Exception("Not enough songs")

        return(niche_tracks)
    
            

