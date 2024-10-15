from scripts.util import load_env

LastFmArtist = dict[str, any]

env = load_env()
LASTFM_API_KEY = env['LASTFM_API_KEY']
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'
