# Module for finding the niche songs for a genre
from scripts.spotify_genre.SpotifyUser import SpotifyUser
from scripts.playlist_maker.PlaylistRequest import PlaylistRequest, Language
from scripts.playlist_maker.Playlist import Playlist, NicheTrack, PlaylistInfo
from scripts.playlist_maker.Artist import Artist
from scripts.util import sleep, RequestType, load_env, get_shuffled_offsets
import musicbrainzngs
import random
from numpy import mean as mean

env = load_env()

"""
Searching Spotify for Track: '不知不覺' by Artist: 'the pancakes'
Spotify Artist ID: 3PRt51b9N0y4akRbx2JfzZ
Retrieved Spotify Artist: The Pancakes (ID: 3PRt51b9N0y4akRbx2JfzZ)
Searching Spotify for Track: 'leave it alone' by Artist: 'the popguns'
"""
# TODO WHAT IS THE ERROR FOR THE PANCAKES WHY GO THE POPGUNS
# TODO - \impl observer patterns n stuff
# TODO - IMPL LOGGER
# TODO - duration check from spotify

global NICHE_APP_URL
global MUSICBRAINZ_MAX_LIMIT_PAGINATION
NICHE_APP_URL                    = 'http://niche-app.net'
MUSICBRAINZ_MAX_LIMIT_PAGINATION = 100

# TODO - Better error handling, overall cleaning, etc
class NicheTrackFinder:
    """Niche Track Finder
        
    Attributes:
        TODO
    """
    def __init__(self, request: PlaylistRequest) -> None:
        """_summary_

        Args:
            request (PlaylistRequest): _description_
        """
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

        self.spotify_user                 = SpotifyUser()
        self.spotipy_methods              = self.spotify_user.user
        self.request                      = request

    def _fetch_artists_from_musicbrainz(self, offset: int = 0) -> list[Artist]:
        """Get a list of Artists from MusicBrainz at the specified offset with an exact tag match.

        Args:
            offset (int, optional): Offset for pagination. Defaults to 0.

        Returns:
            list[Artist]: List of artist objects.
        """
        try:
            ## BEGIN REQUEST ##
            # Enclose the genre tag in double quotes for exact matching
            exact_tag = f'"{self.request.genre}"'
            
            result = self.musicbrainz.search_artists(
                tag    = exact_tag,
                limit  = MUSICBRAINZ_MAX_LIMIT_PAGINATION,
                offset = offset
            )
            sleep(RequestType.MUSICBRAINZ)
            ## END REQUEST ##
            
            current_artists = result.get('artist-list', [])
            artists = []

            for artist in current_artists:
                # Ensure that the artist's language matches the requested language
                if (self.request.language == Language.ANY) or (self._get_artist_language(artist) == self.request.language):
                    a = Artist.from_musicbrainz(artist)
                    artists.append(a)

            print(f"Retrieved {len(artists)} unique artists with tag '{self.request.genre}' from offset {offset}.")
            return artists

        except musicbrainzngs.ResponseError as e:
            print(f"MusicBrainz API error at offset {offset}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error at offset {offset}: {e}")
            return []


    def _find_max_offset_musicbrainz_artists(self, initial_guess: int = 8000) -> int:
        """Get the highest offset where MusicBrainz returns artists.

        Args:
            initial_guess (int, optional): Initial guess for the upper bound. Defaults to 8000.

        Returns:
            int: The highest valid offset where artists are returned.
        """
        # Step 1: Exponential Search to find an upper bound where no artists are returned
        lower = 0
        upper = initial_guess
        step = initial_guess

        while True:
            print(f"Testing offset for upper bound: {upper}")
            artists = self._fetch_artists_from_musicbrainz(offset=upper)
            if artists:
                lower = upper
                step *= 2
                upper += step
                print(f"Artists found at offset {upper - step}. Increasing upper bound to {upper}.")
            else:
                print(f"No artists found at offset {upper}. Upper bound established.")
                break

        # Now perform binary search between lower and upper to find the maximum valid offset
        max_valid_offset = lower
        while lower <= upper:
            mid = (lower + upper) // 2
            print(f"Testing offset: {mid}")
            artists = self._fetch_artists_from_musicbrainz(offset=mid)
            if artists:
                max_valid_offset = mid
                lower = mid + 1
                print(f"Artists found at offset {mid}. Setting new lower bound to {lower}.")
            else:
                upper = mid - 1
                print(f"No artists found at offset {mid}. Setting new upper bound to {upper}.")

        print(f"Maximum valid offset found: {max_valid_offset}")
        return max_valid_offset


    def _artist_listeners_and_plays_valid(self, artist: Artist) -> bool:
        """_summary_

        Args:
            artist (Artist): _description_

        Returns:
            bool: _description_
        """
        listeners = artist.lastfm_artist_listeners
        playcount = artist.lastfm_artist_playcount

        if ((not (listeners and playcount)) or
            ((listeners > self.request.lastfm_listeners_max) and (playcount > self.request.lastfm_playcount_max)) or
            ((listeners < self.request.lastfm_listeners_min) or (playcount < self.request.lastfm_playcount_min)) or
            (artist.lastfm_artist_likeness < self.request.lastfm_likeness_min)):
            print(f'Artist {artist.name} listeners {listeners} or playcount {playcount} invalid')
            return(False)

        return(True)

    def _filter_artists(self, artists: list[Artist]) -> list[Artist]:
        """Filter artists level 1 - Check listeners, plays, genre

        Args:
            artists (list[Artist]): _description_

        Returns:
            list[Artist]: _description_
        """
        return([
            artist for artist in artists if (
                (self._artist_listeners_and_plays_valid(artist)) and
                (artist.artist_in_genre(self.request.genre))
            )
        ])

    def _find_niche_tracks(self) -> list[NicheTrack]:
        """Get a list of niche tracks based on self's attributes

        Returns:
            list[NicheTrack]: A list of niche tracks that align with the playlist request
        """
        # TODO - Pick random num of tracks from artist (edit remaining artists needed and anything w tracks / artist) - get it to go closer to 1 bias ???
        # TODO - If hit max songs per artist, save the rest of the songs just in case playlist not filled? Or have functionality to expand artist top song count?
        #   Hence looking at all artists for genre, and all of their songs
        niche_tracks           = []
        track_cache            = set()
        artist_song_count      = {}  # Dictionary to track number of songs per artist

        desired_song_count   = self.request.playlist_length
        max_songs_per_artist = self.request.max_songs_per_artist

        # Step 1: Find the maximum valid offset using binary search
        max_offset = self._find_max_offset_musicbrainz_artists()
        offsets_list = list(range(0, max_offset, MUSICBRAINZ_MAX_LIMIT_PAGINATION))
        # TODO - Bias to higher offsets or again start caching artists for not fittinf certain criteria
        # TODO - Bias to different offsets based on niche level
        offsets_list = get_shuffled_offsets(offsets_list, self.request.niche_level)

        remaining_artists_needed =  desired_song_count * max_songs_per_artist
        attempts = 0
        max_attempts = 20 * remaining_artists_needed  # Prevent infinite loops

        for i in range(len(offsets_list)):
            if (len(niche_tracks) >= desired_song_count or attempts > max_attempts):
                break

            # Step 2: Randomly select offsets to retrieve artists
            random_offset = offsets_list[i]
            print(f"Attempting to fetch artists at offset {random_offset}.")
            artists = self._fetch_artists_from_musicbrainz(offset = random_offset)

            if(not artists):
                print(f"No artists found at offset {random_offset}.")
                attempts += 1
                continue

            valid_artists = []

            for artist in artists:
                try:
                    artist.attach_artist_lastfm()
                    print(f'Attached lastfm artist {artist.name} from lastfm')
                    valid_artists.append(artist)
                except Exception as e:
                    print(e)

            # for artist in artists:
            #     print(artist['tag_list'])
            #     print(self._get_tags_from_lastfm_artist(artist = artist))
            valid_artists = self._filter_artists(valid_artists)

            # Shuffle artists
            random.shuffle(valid_artists)

            for artist in valid_artists:
                if(len(niche_tracks) >= desired_song_count):
                    break

                try:
                    # Get artist's top tracks from lastfm
                    top_tracks = artist.attach_artist_top_tracks_lastfm()
                except Exception as e:
                    print(e)
                    continue
                if(not top_tracks):
                    print(f"No top tracks found on lastfm for artist: {artist.name}")
                    continue

                # Shuffle tracks to add randomness
                random.shuffle(top_tracks)

                # TODO - Change this to try and attach from all top 10 tracks
                # TODO - Fot this and attach spotify track information and get artist by name and anything else that uses string comp use fuzzy search
                #  Esp for spotify can just to completely fuzzy search since artist can be wrong because we check followers anyways (or maybe not cuz of genre check, so just song name fuzzy)
                try:
                    # Get the spotify artist from the lastfm top tracks (so that we decrease the chance of getting the wrong artist from name search alone)
                    artist.attach_spotify_artist_from_track(top_tracks[0], self.spotipy_methods)
                    print(f'Attached spotify artist {artist.name} from lastfm top track')
                except Exception as e:
                    print(e)
                    break

                for track in top_tracks:
                    # Check if artist already has max allowed songs or more or less than allowed followers
                    if((artist_song_count.get(artist.name, 0) >= max_songs_per_artist) or 
                       (len(niche_tracks) >= desired_song_count) or
                       (artist.spotify_followers > self.request.spotify_followers_max) or
                       (artist.spotify_followers < self.request.spotify_followers_min)):
                        print(f'Artist {artist.name} followers ({artist.spotify_followers}) invalid OR has too many songs OR song count has been reached')
                        break
                    
                    try:
                        track.attach_spotify_track_information(self.spotipy_methods)
                        print(f'Attached spotify track info for {track.name}')
                    except Exception as e:
                        print(e)
                        continue

                    track_key = f"{artist.name}-{track.name}"
                    if(track_key in track_cache):
                        continue
                    track_cache.add(track_key)

                    # CHECK DURATION
                    if ((track.track_length_seconds < self.request.songs_length_min_secs) or (track.track_length_seconds > self.request.songs_length_max_secs)):
                        print(f"Skipping track '{track.name}' by '{artist.name}' due to song length constraints.")
                        continue

                    # # CHECK YEAR PUBLISHED
                    # if (year_published < self.request.songs_min_year_created):
                    #     print(f"Skipping track '{track.name}' by '{artist.name}' due to year published constraints.")
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
                    artist_song_count[artist.name] = artist_song_count.get(artist.name, 0) + 1
                    print(f"Added niche track: {artist.name} - {track.name}")

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
