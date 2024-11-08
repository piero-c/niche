from src.utils.util import load_env, sleep, RequestType, map_language_codes, filter_low_count_entries
from src.utils.musicbrainz_util import MUSICBRAINZ_API_URL
from src.services._shared_classes.PlaylistRequest import Language
import requests
from requests import Response

class MusicBrainzRequests:
    """Class for making requests to MusicBrainz API

    Attributes:
        _MUSICBRAINZ_API_URL
        _USER_AGENT
    """
    def __init__(self) -> None:
        """Initialize object
        """
        env                       = load_env()
        self._MUSICBRAINZ_API_URL = MUSICBRAINZ_API_URL
        self._USER_AGENT          = f'{env['APPLICATION_NAME']}/{env['APPLICATION_VERSION']} ( {env['APPLICATION_CONTACT']} )'

    def _query(self, params: dict[str, any], method: str = "") -> Response:
        """Query MusicBrainz

        Args:
            params (dict[str, any]): Params for API hit
            method (str): Endpoint to hit

        Returns:
            Response: The response as returned by MusicBrainz
        """
        url = self._MUSICBRAINZ_API_URL + method
        headers = {
            'UserAgent': self._USER_AGENT
        }
        ## BEGIN REQUEST ##
        response = requests.get(url, params=params, headers=headers)
        sleep(RequestType.MUSICBRAINZ)
        ## END REQUEST ##

        response.raise_for_status()
        return(response)

    def get_artist_languages(self, mbid: str, pct_min: int = 50) -> dict[Language, float]:
        """Get the languages that an artist sings in

        Args:
            mbid (str): Artist mbid
            pct_min (int, optional): The percentage of their works that must be sung in a language to count the language. Defaults to 50.

        Returns:
            dict[Language, float]: Language: percent of works done in that language
        """
        params = {
            'inc': 'works',
            'fmt': 'json'
        }
        response: Response = self._query(params, f'artist/{mbid}')
        data     = response.json()

        languages: list[str] = []
        works     = data.get('works', [])
        for work in works:
            language_code = work.get('language')
            if(language_code):
                languages.append(language_code)

        return(filter_low_count_entries(map_language_codes(languages), pct_min = pct_min))
