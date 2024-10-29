from scripts.utils.util import load_env, sleep, RequestType, map_language_codes, filter_low_count_entries
from scripts.utils.musicbrainz_util import MUSICBRAINZ_API_URL
from scripts.playlist_maker.PlaylistRequest import Language
import requests

class MusicBrainzRequests:
    def __init__(self) -> None:
        env = load_env()
        self._MUSICBRAINZ_API_URL = MUSICBRAINZ_API_URL
        self._USER_AGENT          = f'{env.APPLICATION_NAME}/{env.APPLICATION_VERSION} ( {env.APPLICATION_CONTACT} )'

    def _query(self, params: dict[str, any], method: str) -> requests.get:
        url = self._MUSICBRAINZ_API_URL + method
        headers = {
            'UserAgent': self._USER_AGENT
        }
        ## BEGIN REQUEST ##
        response = requests.get(url, params=params, headers=headers)
        sleep(RequestType.MUSICBRAINZ)
        ## END REQUEST ##

        return response

    def get_artist_languages(self, mbid) -> list[Language]:
        """
        Retrieves the languages of the artist's works using their MBID.
        """
        params = {
            'inc': 'works',
            'fmt': 'json'
        }
        response = self._query(params, f'artist/{mbid}')
        data     = response.json()

        languages = set()
        works     = data.get('works', [])
        for work in works:
            language_code = work.get('language')
            if(language_code):
                languages.add(language_code)

        return(filter_low_count_entries(map_language_codes(languages), pct_min = 50))
