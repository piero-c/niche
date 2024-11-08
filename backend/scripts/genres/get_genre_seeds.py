from typing import Tuple, List
from src.auth.LastFMRequests import LastFMRequests
from src.auth.MusicBrainzRequests import MusicBrainzRequests
from src.auth.SpotifyUser import spotify_user
import os
from pathlib import Path

inc = 50
lim = 2000

def collect_lastfm_genres(lastfm_requester: LastFMRequests, limit: int = 2000) -> List[str]:
    """Collect up to 2000 genres from Last.fm."""
    all_genres = []
    offset = 0
    while len(all_genres) < limit:
        params = {
            "method": "tag.getTopTags",
            "format": "json",
            "offset": offset,
            "limit" : inc
        }
        response = lastfm_requester._query(params)
        tags = response.json().get("toptags", {}).get("tag", [])
        genres = [tag["name"] for tag in tags]
        all_genres.extend(genres)
        
        if len(tags) < inc:  # No more data to fetch
            break
        offset += inc
    return all_genres

def collect_musicbrainz_genres(musicbrainz_requester: MusicBrainzRequests, limit: int = 2000) -> List[str]:
    """Collect up to 2000 genres from MusicBrainz."""
    all_genres = []
    offset = 0
    while len(all_genres) < limit:
        params = {
            "fmt": "json",
            "limit": inc,  # Max per page for MusicBrainz
            "offset": offset
        }
        response = musicbrainz_requester._query(params, "genre/all")
        genres = [genre["name"] for genre in response.json().get("genres", [])]
        all_genres.extend(genres)
        
        if len(genres) < inc:  # No more data to fetch
            break
        offset += inc
    return all_genres

def collect_spotify_genres() -> List[str]:
    """Collect genres from Spotify (genre seeds)"""
    
    response = spotify_user.client.recommendation_genre_seeds()
    return response.get("genres", [])

def write_genres_to_file(filename: str, genres: List[str]):
    """Writes a list of genres to a file in the ./data/ directory."""
    os.makedirs("scripts/genres/data/", exist_ok=True)  # Ensure the data directory exists
    with open(f"scripts/genres/data/{filename}", "w") as file:
        for genre in genres:
            file.write(f"{genre}\n")

def collect_all_genres(
    lastfm_requester: LastFMRequests,
    musicbrainz_requester: MusicBrainzRequests
) -> Tuple[List[str], List[str], List[str]]:
    """Collect genres from Last.fm, MusicBrainz, and Spotify."""
    lastfm_genres = collect_lastfm_genres(lastfm_requester, lim)
    musicbrainz_genres = collect_musicbrainz_genres(musicbrainz_requester, lim)
    spotify_genres = collect_spotify_genres()


    # Write each genre list to its own file in ./data/
    write_genres_to_file(Path("LASTFM"), lastfm_genres)
    write_genres_to_file(Path("MUSICBRAINZ"), musicbrainz_genres)
    write_genres_to_file(Path("SPOTIFY"), spotify_genres)

    return lastfm_genres, musicbrainz_genres, spotify_genres

# Example usage (ensure classes are initialized properly)
lastfm_requester = LastFMRequests()
musicbrainz_requester = MusicBrainzRequests()

all_genres = collect_all_genres(lastfm_requester, musicbrainz_requester)
