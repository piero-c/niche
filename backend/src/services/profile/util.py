
from typing import Optional
from urllib.parse import urlparse, parse_qs
import re


def extract_playlist_id(playlist_link: str) -> Optional[str]:
    """
    Extracts the Spotify playlist ID from a playlist URL.

    Args:
        playlist_link (str): The URL to the Spotify playlist.

    Returns:
        Optional[str]: The playlist ID if extraction is successful; otherwise, None.
    """
    # Spotify playlist URL patterns
    patterns = [
        r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)",
        r"spotify:playlist:([a-zA-Z0-9]+)"
    ]

    for pattern in patterns:
        match = re.match(pattern, playlist_link)
        if match:
            return match.group(1)

    # Attempt to parse URL for query parameters (e.g., share links)
    parsed_url = urlparse(playlist_link)
    query_params = parse_qs(parsed_url.query)
    if 'list' in query_params:
        return query_params['list'][0]

    return None
