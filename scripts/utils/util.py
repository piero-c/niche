from dotenv import load_dotenv
import os
from enum import Enum
import time
import numpy as np
from scripts.playlist_maker.PlaylistRequest import NicheLevel

# Request type for API hits
RequestType = Enum('RequestTypes', ['LASTFM', 'MUSICBRAINZ', 'SPOTIFY'])

# As per rate limiting guidelines
global API_SLEEP_LENGTHS
API_SLEEP_LENGTHS = {
    RequestType.LASTFM     : 0.2,
    RequestType.MUSICBRAINZ: 1,
    RequestType.SPOTIFY    : 0.25
}

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
    """Load environment.

    Returns:
        dict[str, str]: Environment.
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

# TODO - Make this some kinda publisher observer pattern?
def sleep(type: RequestType) -> None:
    """Schleep based on request type.

    Args:
        type (RequestType): The type of API request.
    """
    time.sleep(API_SLEEP_LENGTHS[type])

def convert_ms_to_s(ms: int) -> int:
    return ms // 1000

def strcomp(*strings: str) -> bool:
    first = strings[0].lower()
    return all(s.lower() == first for s in strings)

def shuffle_with_percentile_bias_numpy(
    lst: list[int],
    percentile: float = 50.0,
    spread: float = 20.0,
    random_seed: int = None
) -> list[int]:
    """
    Shuffle a list with a bias towards elements around a specified percentile.
    
    Args:
        lst (List[T]): The ordered list to shuffle.
        percentile (float, optional): The percentile (0 to 100) around which to center the shuffle bias.
                                      Defaults to 50.0 (median).
        spread (float, optional): The standard deviation controlling the spread of the bias.
                                  Higher values make the bias broader. Defaults to 10.0.
        random_seed (int, optional): Seed for the random number generator for reproducibility.
                                     Defaults to None.
    
    Raises:
        ValueError: If `percentile` is not between 0 and 100.
        ValueError: If `spread` is negative.
    
    Returns:
        List[T]: The shuffled list with bias towards the specified percentile.
    """
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100.")
    if spread < 0:
        raise ValueError("spread must be non-negative.")
    
    n = len(lst)
    if n == 0:
        return []
    if n == 1:
        return lst.copy()
    
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Calculate the target index based on percentile
    target_idx = (percentile / 100) * (n - 1)
    
    # Compute distances from the target index
    indices = np.arange(n)
    distances = np.abs(indices - target_idx)
    
    # Assign weights using a Gaussian distribution
    weights = np.exp(- (distances ** 2) / (2 * spread ** 2))
    
    # Normalize weights to sum to 1
    weights /= weights.sum()
    
    # Perform weighted random shuffle using numpy's choice
    shuffled_indices = np.random.choice(indices, size=n, replace=False, p=weights)
    
    # Map shuffled indices to elements
    shuffled = [lst[i] for i in shuffled_indices]
    return shuffled

# TODO - Mess with standard deviation and percentiles - can remove this once we start caching artists that don't fit a certain request
# TODO - Make sure this is actually working (for current req should be ordered centered around 6200)
def get_shuffled_offsets(offsets: list[int], niche_level: NicheLevel) -> list[int]:
    """_summary_

    Args:
        offsets (list[int]): _description_
        niche_level (NicheLevel): _description_

    Returns:
        list[int]: _description_
    """
    percentiles = {
        NicheLevel.VERY: 25,
        NicheLevel.MODERATELY: 17,
        NicheLevel.ONLY_KINDA: 10
    }
    return shuffle_with_percentile_bias_numpy(offsets, percentiles[niche_level])
