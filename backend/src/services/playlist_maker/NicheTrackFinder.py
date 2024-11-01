# Module for finding the niche songs for a genre
from auth.SpotifyUser import SpotifyUser
from auth.MusicBrainzRequests import MusicBrainzRequests

from services.playlist_maker.PlaylistRequest import PlaylistRequest, Language
from services.playlist_maker.Playlist import Playlist, NicheTrack, PlaylistInfo
from services.playlist_maker.Artist import Artist

from utils.util import load_env

from db.DB import DB
from db.ArtistsDAO import ArtistsDAO

import random
from numpy import mean as mean

from utils.logger import logger
env    = load_env()

global NICHE_APP_URL
NICHE_APP_URL = 'http://niche-app.net'

class NicheTrackFinder:
    """Niche Track Finder
        
    Attributes:
        request
        user
        artistsDAO
    """
    def __init__(self, request: PlaylistRequest, user: SpotifyUser) -> None:
        """Initialize the finder

        Args:
            request (PlaylistRequest): The playlist request
            user (SpotifyUser): Spotify Authenticated User
        """
        self.request         = request
        self.user            = user

        db_instance          = DB()
        self.artistsDAO      = ArtistsDAO(db_instance)


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

    def _artist_listeners_and_plays_valid(self, artist: Artist) -> bool:
        """Valid according to request for nicheness level
        """
        listeners = artist.lastfm_artist_listeners
        playcount = artist.lastfm_artist_playcount

        if((not (listeners and playcount)) or
            ((listeners > self.request.lastfm_listeners_max) and (playcount > self.request.lastfm_playcount_max)) or
            ((listeners < self.request.lastfm_listeners_min) or (playcount < self.request.lastfm_playcount_min)) or
            (artist.lastfm_artist_likeness < self.request.lastfm_likeness_min)):
            logger.warning(f'Artist {artist.name} listeners {listeners} or playcount {playcount} or likeness {artist.lastfm_artist_likeness} invalid')
            return(False)

        return(True)

    def _find_niche_tracks(self) -> list[NicheTrack]:
        """Make the playlist

        Raises:
            Exception: Not enough songs could be added

        Returns:
            list[NicheTrack]: List of niche tracks
        """
        niche_tracks      = []

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
                try:
                    artist.attach_artist_lastfm()
                    logger.info(f'Attached lastfm artist {artist.name} from lastfm')
                    valid_artists.append(artist)
                except Exception as e:
                    logger.error(e)

            valid_artists = [
                artist for artist in valid_artists if(
                    (self._artist_listeners_and_plays_valid(artist)) and
                    # This is mostly to ensure that if we attached artist by name, it is the artist we were looking for
                    (artist.artist_in_lastfm_genre(self.request.genre))
                )
            ]

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
                    # Check if artist already has max allowed songs or more or less than allowed followers
                    if((len(niche_tracks) >= desired_song_count) or
                       (artist.spotify_followers > self.request.spotify_followers_max) or
                       (artist.spotify_followers < self.request.spotify_followers_min)):
                        logger.warning(f'Artist {artist.name} followers ({artist.spotify_followers}) invalid OR has too many songs OR song count has been reached')
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
                        logger.warning(f"Artist does not sing in {self.request.language}")
                        break

                    # TODO
                    # # CHECK YEAR PUBLISHED
                    # if(year_published < self.request.songs_min_year_created):
                    #     logger.warning(f"Skipping track '{track.name}' by '{artist.name}' due to year published constraints.")
                    #     continue

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
                    logger.info(f"ADDED NICHE TRACK: {artist.name} - {track.name}")
                    logger.info(f"TRACKS ADDED: {len(niche_tracks)}")
                    logger.info(f"RATIO: {(len(niche_tracks) / ((i + 1) * artist_increment_count)) * 100}%")


        if(len(niche_tracks) >= desired_song_count):
            return(niche_tracks)
        else:
            raise Exception('Couldn\'t find enough songs')

    def _get_playlist_info(self) -> PlaylistInfo:
        """Get the info for the playlist

        Returns:
            PlaylistInfo: the info
        """
        # TODO - Make the names unique based on the user? Like indie whatever 1
        return({
            'name': f'Niche {self.request.genre} Songs',
            'description': f'Courtesy of the niche app :) ({NICHE_APP_URL})'
        })

    def create_playlist(self) -> Playlist:
        """Create the playlist of niche songs based on the request

        Returns:
            Playlist: The playlist
        """
        tracks = self._find_niche_tracks()
        playlist_info = self._get_playlist_info()
        return(Playlist(tracks, playlist_info, self.user))
