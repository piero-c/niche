from scripts.utils.util import load_env, sleep, RequestType
from scripts.utils.lastfm_util import LastFmArtist
import requests
from requests import Response

class LastFMRequests:
    """To create requests to the LastFM API

    Attributes:
        _LASTFM_API_KEY
        _LASTFM_API_URL
    """
    def __init__(self) -> None:
        """Initialize the object
        """
        env                  = load_env()
        self._LASTFM_API_KEY = env['LASTFM_API_KEY']
        self._LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'

    def _query(self, params: dict[str, any], method: str) -> Response:
        """Query LastFM API

        Args:
            params (dict[str, any]): Params for query
            method (str): The endpoint to hit

        Returns:
            Response: Response from the API
        """
        url                   = self._LASTFM_API_URL + method
        paramsCopy            = params.copy()
        paramsCopy['api_key'] = self._LASTFM_API_KEY
        ## BEGIN REQUEST ##
        response = requests.get(url, params=paramsCopy)
        sleep(RequestType.LASTFM)
        ## END REQUEST ##

        response.raise_for_status()
        return(response)

    def get_lastfm_artist_data(self, baseParams: dict, name: str = "", mbid: str = "") -> LastFmArtist:
        """Collect artist object from lastfm by name or mbid

        Pre:
            name xor mbid

        Args:
            baseParams (dict): Base params for the call
            name (str, optional): artist name. Defaults to "".
            mbid (str, optional): artist mbid. Defaults to "".

        Returns:
            LastFmArtist: The artist as returned by LastFM
        """
        assert(not(name and mbid) and (name or mbid))
        params = baseParams.copy()

        if(mbid):
            params["mbid"] = mbid
        elif(name):
            params["artist"] = name

        response: Response = self._query(params)
        api_data = response.json()
        
        return(api_data)
