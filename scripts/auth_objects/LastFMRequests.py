from scripts.utils.util import load_env, sleep, RequestType
from scripts.utils.lastfm_util import LastFmArtist
import requests

class LastFMRequests:
    def __init__(self) -> None:
        env = load_env()
        self._LASTFM_API_KEY = env['LASTFM_API_KEY']
        self._LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'

    def _query(self, params: dict[str, any]) -> requests.get:
        paramsCopy = params.copy()
        paramsCopy['api_key'] = self._LASTFM_API_KEY
        ## BEGIN REQUEST ##
        response = requests.get(self._LASTFM_API_URL, params=paramsCopy)
        sleep(RequestType.LASTFM)
        ## END REQUEST ##

        return response

    def get_lastfm_data(self, type: str, value: str, baseParams: dict) -> LastFmArtist:
        """_summary_

        Args:
            type (str): _description_

        Returns:
            LastFmArtist: _description_
        """
        params = baseParams.copy()

        if (type == 'mbid'):
            params["mbid"] = value
        elif (type == 'name'):
            params["artist"] = value

        response = self._query(params)
        if (response.status_code == 200):
            api_data = response.json()
        
        return(api_data)
