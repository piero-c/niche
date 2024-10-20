# Module for finding the niche songs for a genre
from scripts.auth_objects.SpotifyUser import SpotifyUser

from scripts.playlist_maker.PlaylistRequest import PlaylistRequest
from scripts.playlist_maker.Playlist import Playlist, NicheTrack, PlaylistInfo
from scripts.playlist_maker.Artist import Artist

from scripts.utils.util import load_env, get_shuffled_offsets

from scripts.db.DB import DB
from scripts.db.ArtistsDAO import ArtistsDAO
from bson.objectid import ObjectId

import random
from numpy import mean as mean

env = load_env()

global NICHE_APP_URL
NICHE_APP_URL = 'http://niche-app.net'

class NicheTrackFinder:
    """Niche Track Finder
        
    Attributes:
        TODO
    """
    def __init__(self, request: PlaylistRequest, user: SpotifyUser) -> None:
        """_summary_

        Args:
            request (PlaylistRequest): _description_
        """
        self.request         = request
        self.user            = user

        db_instance          = DB()
        self.artistsDAO      = ArtistsDAO(db_instance)


    def _fetch_artists_from_musicbrainz(self) -> list[Artist]:
        try:
            artist_list = []
            artists = self.artistsDAO.get_artists_in_genre(self.request.genre)
            for artist in artists:
                try:
                    artist_list.append(Artist.from_musicbrainz(artist, self.user))
                except Exception as e:
                    print(f"Could not create artist: {e}")
            return(artist_list)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return([])

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
            print(f'Artist {artist.name} listeners {listeners} or playcount {playcount} or likeness {artist.lastfm_artist_likeness} invalid')
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
                (artist.artist_in_lastfm_genre(self.request.genre))
            )
        ])

    def _find_niche_tracks(self) -> list[NicheTrack]:
        """Get a list of niche tracks based on self's attributes

        Returns:
            list[NicheTrack]: A list of niche tracks that align with the playlist request
        """
        # TODO - Max attempts??
        # TODO - Pick random num of tracks from artist (edit remaining artists needed and anything w tracks / artist) - get it to go closer to 1 bias ???
        # TODO - If hit max songs per artist, save the rest of the songs just in case playlist not filled? Or have functionality to expand artist top song count?
        #   Hence looking at all artists for genre, and all of their songs
        niche_tracks           = []
        track_cache            = set()
        artist_song_count      = {}  # Dictionary to track number of songs per artist

        desired_song_count   = self.request.playlist_length
        max_songs_per_artist = self.request.max_songs_per_artist

        artist_increment_count = 25

        artists_list = self._fetch_artists_from_musicbrainz()
        # Using list comprehension with padding
        artists_sublists = [artists_list[i:i+artist_increment_count] if len(artists_list[i:i+artist_increment_count]) == artist_increment_count else artists_list[i:i+artist_increment_count] + [None]*(artist_increment_count - len(artists_list[i:i+artist_increment_count])) for i in range(0, len(artists_list), artist_increment_count)]

        offsets_list = list(range(0, len(artists_sublists)))
        # TODO - Bias to higher offsets or again start caching artists for not fittinf certain criteria
        # TODO - Bias to different offsets based on niche level
        offsets_list = get_shuffled_offsets(offsets_list, self.request.niche_level)

        for i in range(len(offsets_list)):
            print(f'artists checked: {i * artist_increment_count}')
            if (len(niche_tracks) >= desired_song_count):
                break

            random_offset = offsets_list[i]
            artists = artists_sublists[random_offset]

            print(f'Checking offset {random_offset} of {len(offsets_list)}')

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

                attached = False
                # TODO - Change this to try and attach from all top 10 tracks
                # TODO - Fot this and attach spotify track information and get artist by name and anything else that uses string comp use fuzzy search
                #  Esp for spotify can just to completely fuzzy search since artist can be wrong because we check followers anyways (or maybe not cuz of genre check, so just song name fuzzy)
                for top_track in top_tracks:
                    try:
                        # Get the spotify artist from the lastfm top tracks (so that we decrease the chance of getting the wrong artist from name search alone)
                        artist.attach_spotify_artist_from_track(top_track)
                        spotify_artist_id = artist.spotify_artist_id
                        print(f'Attached spotify artist {artist.name} from lastfm top track')
                        attached = True
                        break
                    except Exception as e:
                        print(e)
                        break

                if (not attached):
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
                        track.attach_spotify_track_information(spotify_artist_id)
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
                    print(f"ADDED NICHE TRACK: {artist.name} - {track.name}")
                    print(f"TRACKS ADDED: {len(niche_tracks)}")
                    print(f"RATIO: {(len(niche_tracks) / ((i + 1) * artist_increment_count)) * 100}%")


        if (len(niche_tracks) >= desired_song_count):
            return(niche_tracks)
        else:
            raise Exception('Couldn\'t find enough songs')

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
        return(Playlist(tracks, playlist_info, self.user))
