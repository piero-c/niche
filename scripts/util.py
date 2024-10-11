from dotenv import load_dotenv
import os

def merge_dicts_with_weight(dicts: list[dict[any, int|float]], weights: list[int]) -> dict[any, int|float]:
    """Merge a list of dictionaries into one, considering the weight of each.

    Args:
        dicts (list[dict[any, int | float]]): The dictionaries.
        weights (list[int]): The weights.

    Returns:
        dict[any, int|float]: The merged dict.
    """
    assert(len(dicts) == len(weights))
    merged_dict = {}
    for (d, weight) in zip(dicts, weights):
        for key, value in d.items():
            merged_dict[key] = merged_dict.get(key, 0) + value * weight
    
    return merged_dict

def load_env() -> dict[str, str]:
    """Load environment

    Returns:
        dict[str, str]: Environment
    """
    load_dotenv()
    return({
        #SPOTIFY
        "SPOTIFY_CLIENT_ID"    : os.getenv('SPOTIFY_CLIENT_ID'),
        "SPOTIFY_CLIENT_SECRET": os.getenv('SPOTIFY_CLIENT_SECRET'),
        "SPOTIFY_REDIRECT_URI" : os.getenv('SPOTIFY_REDIRECT_URI'),
        "SCOPE"                : "user-top-read user-follow-read playlist-modify-public playlist-modify-private",
        "CACHE_PATH"           : ".cache",
        #LASTFM
        "LASTFM_API_KEY": os.getenv('LASTFM_API_KEY'),
        #APPLICATION(MUSICBRAINZ)
        "APPLICATION_NAME"   : os.getenv("APPLICATION_NAME"),
        "APPLICATION_VERSION": os.getenv("APPLICATION_VERSION"),
        "APPLICATION_CONTACT": os.getenv("APPLICATION_CONTACT"),
    })