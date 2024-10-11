# Module for finding the niche songs for a genre
from scripts.util import load_env
from scripts.spotify_genre.SpotifyUser import SpotifyUser
from scripts.playlist_maker.PlaylistRequest import PlaylistRequest, Language
from scripts.playlist_maker.Playlist import Playlist, NicheTrack, PlaylistInfo
import time
import musicbrainzngs
from typing import TypedDict
import requests
import random
from numpy import mean as mean
from urllib.parse import quote_plus
from datetime import datetime

class ArtistObject(TypedDict):
    name          : str
    musicbrainz_id: str

class LastFMTrackInfo(TypedDict):
    name            : str
    playcount       : int
    listeners       : int
    duration_seconds: int

global LASTFM_API_URL
global MUSICBRAINZ_MAX_LIMIT_PAGINATION
global MS_TO_SECS_DIVISOR
global NICHE_APP_URL
LASTFM_API_URL                   = 'http://ws.audioscrobbler.com/2.0/'
MUSICBRAINZ_MAX_LIMIT_PAGINATION = 100
MS_TO_SECS_DIVISOR               = 1000
NICHE_APP_URL                    = 'http://niche-app.net'

class NicheTrackFinder:
    """Niche Track Finder
        
    Attributes:
        TODO
    """
    def __init__(self, request: PlaylistRequest) -> None:
        env = load_env()
        # Musicbrainz user agent identification
        APPLICATION_NAME    = env['APPLICATION_NAME']
        APPLICATION_VERSION = env['APPLICATION_VERSION']
        APPLICATION_CONTACT = env['APPLICATION_CONTACT']

        self.musicbrainz = musicbrainzngs
        # MusicBrainz Configuration (global)
        self.musicbrainz.set_useragent(
            APPLICATION_NAME,
            APPLICATION_VERSION,
            APPLICATION_CONTACT
        )
        self.LASTFM_API_KEY = env['LASTFM_API_KEY']

        self.spotify_user                 = SpotifyUser()
        self.spotipy_methods              = self.spotify_user.user
        self.api_sleep_length             = 0.25
        self.request                      = request
        self.musicbrainz_limit_pagination = MUSICBRAINZ_MAX_LIMIT_PAGINATION

    # TODO - Make this some kinda publisher observer pattern?
    def _sleep(self) -> None:
        """Schleep so I don't get rate limited
        """
        time.sleep(self.api_sleep_length)

    def _get_artist_language(musicbrainzArtist: dict) -> Language:
        """Return the language of the artist.

        Args:
            musicbrainzArtist (dict): MusicBrainz artist object.

        Returns:
            Language: The artist's language.
        """
        pass
    
    def _fetch_artists_from_musicbrainz(self, offset: int = 0) -> list[ArtistObject]:
        """Get a list of ArtistObject s from MusicBrainz at the offset.

        Args:
            offset (int, optional): Offset. Defaults to 0.

        Returns:
            list[ArtistObject]: List of artist objects.
        """
        try:
            ## BEGIN REQUEST ##
            result = self.musicbrainz.search_artists(
                tag    = self.request.genre,
                limit  = self.musicbrainz_limit_pagination,
                offset = offset
            )
            self._sleep()
            ## END REQUEST ##
            current_artists = result.get('artist-list', [])
            artists = []

            for artist in current_artists:
                if((self.request.language == Language.ANY) or (self._get_artist_language(artist) != self.request.language)):
                    artist_name    = artist.get('name')
                    musicbrainz_id = artist.get('id')
                    artists.append({'name': artist_name, 'musicbrainz_id': musicbrainz_id})

            print(f"Retrieved {len(artists)} unique artists from offset {offset}.")
            return(artists)
        except musicbrainzngs.ResponseError as e:
            print(f"MusicBrainz API error at offset {offset}: {e}")
            return([])
        except Exception as e:
            print(f"Unexpected error at offset {offset}: {e}")
            return([])
    

    def _find_max_offset_musicbrainz_artists(self, initial_guess: int = 5000) -> int:
        """Get the highest offset where musicbrainz returns artists.

        Args:
            initial_guess (int, optional): Initial guess. Defaults to 5000.

        Returns:
            int: The highest offset.
        """
        tolerance = self.musicbrainz_limit_pagination
        lower = 0
        upper = initial_guess
        max_valid_offset = 0

        while lower <= upper:
            mid = (lower + upper) // 2
            print(f"Testing offset: {mid}")
            artists = self._fetch_artists_from_musicbrainz(offset=mid)
            if(artists):
                max_valid_offset = mid
                lower = mid + 1
            else:
                upper = mid - 1

            # If the search range is within the tolerance, stop searching
            if(upper - lower < tolerance):
                break

        print(f"Maximum valid offset found: {max_valid_offset}")
        return(max_valid_offset)
    
    def _get_artist_spotify_id(self, artist: ArtistObject) -> str:
        """Get artist spotify id.

        Args:
            artist (ArtistObject): Artist object.

        Returns:
            str: The spotify artist id.
        """
        try:
            ## BEGIN REQUEST ##
            results = self.spotipy_methods.search(q=f'artist:"{artist['name']}"', type='artist', limit=1)
            self._sleep()
            ## END REQUEST ##
            items = results.get('artists', {}).get('items', [])
            if(not items):
                print(f"No Spotify ID found for artist: {artist['name']}")
                return(None)
            spotify_id = items[0]['id']
            return(spotify_id)
        except Exception as e:
            print(f"Error searching for artist '{artist['name']}' on Spotify: {e}")
            return(None)

    def _get_artist_top_tracks_spotify(self, artist_id: str, country: str = 'US', limit: int = 10) -> dict:
        """Get the artists top tracks on spotify.

        Args:
            artist_id (str): spotify artist id.
            country (str, optional): Only content that is available in this country will be returned. Defaults to 'US'.
            limit (int, optional): Max number of songs to return. Defaults to 10.

        Returns:
            dict: Dict of tracks
        """
        try:
            results = self.spotipy_methods.artist_top_tracks(artist_id, country = country)
            tracks = results.get('tracks', [])
            if(not tracks):
                print(f"No top tracks found on Spotify for artist ID: {artist_id}")
                return([])
            return(tracks[:limit])
        except Exception as e:
            print(f"Error fetching top tracks for artist ID {artist_id} on Spotify: {e}")
            return([])

    def _get_track_info_lastfm(self, artist_name: str, track_name: str) -> LastFMTrackInfo:
        """Retrieve track info from LastFM.

        Args:
            artist_name (str): Artist name.
            track_name (str): Track name.

        Returns:
            LastFMTrackInfo: Object describing the track
        """
        params = {
            'method': 'track.getInfo',
            'api_key': self.LASTFM_API_KEY,
            'artist': artist_name,
            'track': track_name,
            'format': 'json'
        }
        try:
            ## BEGIN REQUEST ##
            response = requests.get(LASTFM_API_URL, params=params)
            self._sleep()
            ## END REQUEST ##
            response.raise_for_status()
            data = response.json()
            if('error' in data):
                print(f"Last.fm error for '{artist_name} - {track_name}': {data.get('message', 'Unknown error')}")
                return{}

            track_info = data.get('track', {})
            playcount = int(track_info.get('playcount', 0))
            listeners = int(track_info.get('listeners', 99999999))
            name = track_info.get('name', '')
            duration_seconds = int(track_info.get('duration', 0)) / MS_TO_SECS_DIVISOR
            return({
                'playcount'       : playcount,
                'listeners'       : listeners,
                'name'            : name,
                'duration_seconds': duration_seconds,
            })
        except requests.exceptions.RequestException as e:
            print(f"HTTP error while fetching track info for '{artist_name} - {track_name}': {e}")
            return{}
        except ValueError:
            print(f"Invalid playcount value for '{artist_name} - {track_name}'.")
            return{}

    def _find_niche_tracks(self) -> list[NicheTrack]:
        """Get a list of niche tracks based on self's attributes

        Returns:
            list[NicheTrack]: A list of niche tracks that align with the playlist request
        """
        # TODO - Pick random num of tracks from artist (edit remaining artists needed and anything w tracks / artist) - get it to go closer to 1 bias
        # TODO - If hit max songs per artist, save the rest of the songs just in case playlist not filled? Or have functionality to expand artist top song count?
        #   Hence looking at all artists for genre, and all of their songs
        niche_tracks = []
        track_cache = set()
        artist_song_count = {}  # Dictionary to track number of songs per artist

        desired_song_count = self.request.playlist_length
        max_songs_per_artist = self.request.max_songs_per_artist

        # Step 1: Find the maximum valid offset using binary search
        max_offset = self._find_max_offset_musicbrainz_artists()

        offset_intervals = [max_offset, max_offset * 2 // 3, max_offset * 1 // 3, 0]

        for i in range(1, len(offset_intervals)):
            if (len(niche_tracks) >= desired_song_count):
                break
            offset_low   = offset_intervals[i]
            offset_high  = offset_intervals[i-1]
            offsets_list = list(range(offset_low, offset_high + 1, self.musicbrainz_limit_pagination))
            print(f"Selecting artists from offset {offset_low} to {offset_high}.")

            # Step 3: Randomly select offsets to retrieve artists
            # To avoid making too many API calls, we'll sample offsets instead of iterating through all
            remaining_artists_needed =  desired_song_count * max_songs_per_artist
            attempts = 0
            max_attempts = 20 * remaining_artists_needed  # Prevent infinite loops

            while len(niche_tracks) < desired_song_count and attempts < max_attempts:
                # Get a random offset (for musicbrainz artists), then delete it from the list
                random_offset_idx = random.randint(0, len(offsets_list) - 1)
                random_offset = offsets_list[random_offset_idx]
                del offsets_list[random_offset_idx]

                print(f"Attempting to fetch artists at offset {random_offset}.")
                artists = self._fetch_artists_from_musicbrainz(offset = random_offset)

                if(not artists):
                    print(f"No artists found at offset {random_offset}.")
                    attempts += 1
                    continue

                for artist in artists:
                    if(len(niche_tracks) >= desired_song_count):
                        break

                    artist_name = artist['name']
                    if(not artist_name):
                        continue

                    spotify_id = self._get_artist_spotify_id(artist)

                    if(not spotify_id):
                        continue

                    try:
                        ## BEGIN REQUEST ##
                        spotify_artist = self.spotipy_methods.artist(spotify_id)
                        self._sleep()
                        ## END REQUEST ##
                        popularity = spotify_artist.get('popularity', 100)  # Default to 100 if(not found
                        if(popularity > self.request.spotify_popularity_max):
                            print(f"Skipping artist '{artist_name}' due to high popularity ({popularity}).")
                            continue
                    except Exception as e:
                        print(f"Error retrieving Spotify data for artist '{artist_name}': {e}")
                        continue

                    print(f"Processing artist: {artist_name} (Spotify Popularity: {popularity})")

                    # Get artist's top tracks from Spotify
                    top_tracks = self._get_artist_top_tracks_spotify(spotify_id)
                    if(not top_tracks):
                        print(f"No top tracks found on Spotify for artist: {artist_name}")
                        continue

                    # Shuffle tracks to add randomness
                    random.shuffle(top_tracks)

                    for track in top_tracks:
                        # Check if artist already has max allowed songs
                        if((artist_song_count.get(artist_name, 0) >= max_songs_per_artist) or (len(niche_tracks) >= desired_song_count)):
                            break

                        track_name = track.get('name')
                        if(not track_name):
                            continue

                        track_key = f"{artist_name}-{track_name}"
                        if(track_key in track_cache):
                            continue
                        track_cache.add(track_key)

                        # Retrieve info from Last.fm
                        track_info       = self._get_track_info_lastfm(artist_name, track_name)
                        if (not track_info.get('playcount', None)):
                            continue
                        playcount        = track_info['playcount']
                        listeners        = track_info['listeners']
                        duration_seconds = track_info['duration_seconds']
                        # TODO - YEAR PUBLISHED

                        # CHECK DURATION
                        if ((duration_seconds < self.request.songs_length_min_secs) or (duration_seconds > self.request.songs_length_max_secs)):
                            print(f"Skipping track '{track_name}' by '{artist_name}' due to song length constraints.")
                            continue

                        # # CHECK YEAR PUBLISHED
                        # if (year_published < self.request.songs_min_year_created):
                        #     print(f"Skipping track '{track_name}' by '{artist_name}' due to year published constraints.")
                        #     continue

                        # CHECK PLAYCOUNT
                        if((playcount < self.request.lastfm_playcount_min) or (playcount > self.request.lastfm_playcount_max) or (listeners == 0)):
                            print(f"Skipping track '{track_name}' by '{artist_name}' due to playcount constraints.")
                            continue

                        likeness = playcount / listeners if listeners > 0 else 0

                        # CHECK LIKENESS
                        if(likeness >= self.request.lastfm_likeness_max):
                            print(f"Skipping track '{track_name}' by '{artist_name}' due to likeness constraint.")
                            continue

                        # TODO - HERE Get spotify URI to NicheTrack def and here then go to chat and create the playlist(take the current prompt as inspo), then want the API to basically return the playlist link and have the web playback sdk show it and then option to save which will b another endpoint like DELETE playlist yaknow.
                        #  TODO -  Ou wait easy way make the playlist public then if they wanna keep it post a thing to api to change it to private (public so can see on sdk web play) and if dont wanna keep it delete it
                        #               GOOD TODO NO EDITS HAHAHAH ON NICHE_WORKING ALL HERE NICE
                        # Add track to niche_tracks
                        niche_track = {
                            'artist'     : artist_name,
                            'track'      : track_name,
                            'playcount'  : playcount,
                            'listeners'  : listeners,
                            'likeness'   : likeness,
                            'spotify_uri': track.get('uri', ''),
                            'spotify_url': track.get('external_urls', {}).get('spotify', ''),
                            'lastfm_url' : f"https://www.last.fm/music/{quote_plus(artist_name)}/_/{quote_plus(track_name)}"
                        }
                        niche_tracks.append(niche_track)
                        artist_song_count[artist_name] = artist_song_count.get(artist_name, 0) + 1
                        print(f"Added niche track: {artist_name} - {track_name}")

                attempts += 1

        return(niche_tracks)

    def _get_playlist_info(self) -> PlaylistInfo:
        """Generate playlist info based on self.

        Returns:
            PlaylistInfo: Playlist info.
        """
        # TODO - Make the names unique based on the user? Like indie whatever 1
        return({
            'name': f'Niche {self.request.genre} Songs',
            'description': f'Courtesy of the niche app :) ({NICHE_APP_URL})'
        })

    def create_playlist(self) -> Playlist:
        """Create and return a playlist for the user based on self.

        Returns:
            Playlist: The playlist.
        """
        tracks = self._find_niche_tracks()
        playlist_info = self._get_playlist_info()
        return(Playlist(tracks, playlist_info, self.spotify_user))
