from src.services.genre_handling.valid_genres import convert_genre
MusicBrainzArtist = dict[str, any]

MUSICBRAINZ_API_URL              = 'https://musicbrainz.org/ws/2/'
MUSICBRAINZ_MAX_LIMIT_PAGINATION = 100

def get_mb_genre(spotify_genre: str = "") -> str:
    return(convert_genre('SPOTIFY', 'MUSICBRAINZ', spotify_genre))


