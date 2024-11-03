from dotenv import load_dotenv
import os
from enum import Enum
import time
import pycountry
from bidict import bidict

NICHE_APP_URL = 'http://niche-app.net'

# Enumerations for request
Language       = Enum('Language', ['ANY', 'ENGLISH', 'OTHER'])
LANGMAP: bidict = bidict({
    'English': Language.ENGLISH,
    'Any'    : Language.ANY,
    'Other'  : Language.OTHER
})

NicheLevel     = Enum('NicheLevel', ['VERY', 'MODERATELY', 'ONLY_KINDA'])
NICHEMAP: bidict = bidict({
    'Very'      : NicheLevel.VERY,
    'Moderately': NicheLevel.MODERATELY,
    'Only Kinda': NicheLevel.ONLY_KINDA
})

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
    # Do the thing
    for (d, weight) in zip(dicts, weights):
        for key, value in d.items():
            merged_dict[key] = merged_dict.get(key, 0) + value * weight
    
    return(merged_dict)

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
        "SCOPE"                : "user-top-read user-follow-read playlist-modify-public playlist-modify-private ugc-image-upload",
        "CACHE_PATH"           : ".cache",
        #LASTFM
        "LASTFM_API_KEY": os.getenv('LASTFM_API_KEY'),
        #APPLICATION(MUSICBRAINZ)
        "APPLICATION_NAME"   : os.getenv("APPLICATION_NAME"),
        "APPLICATION_VERSION": os.getenv("APPLICATION_VERSION"),
        "APPLICATION_CONTACT": os.getenv("APPLICATION_CONTACT"),
    })

def sleep(type: RequestType) -> None:
    """Schleep based on request type. So no get IP banned.

    Args:
        type (RequestType): The type of API request.
    """
    time.sleep(API_SLEEP_LENGTHS[type])

def convert_ms_to_s(ms: int) -> int:
    """Convert ms to s

    Args:
        ms (int): ms

    Returns:
        int: s
    """
    return(ms // 1000)

def strcomp(*strings: str) -> bool:
    """Return true if all strings are equal case-insensitive

    Returns:
        bool: Are they equal?
    """
    first = strings[0].lower()
    return(all(s.lower() == first for s in strings))

def convert_language_to_language_enum(language: str) -> Language:
    """Convert language str to Language enum class

    Args:
        language (str): language str

    Returns:
        Language: Language enum class
    """
    if(LANGMAP.get(language, None)):
        return(LANGMAP.get(language))
    return(Language.OTHER)

def map_language_codes(language_codes: list[str]) -> dict[Language, int]:
    """
    Maps ISO 639-3 language codes to full language names and counts occurrences.

    Args:
        language_codes: A list of language codes.

    Returns:
        A dictionary where keys are language names and values are counts.
    """
    language_counts: dict[str, int] = {}
    for code in language_codes:
        try:
            language = pycountry.languages.get(alpha_3=code)
            if language and hasattr(language, 'name'):
                language_name = language.name
            else:
                # Handle special cases or unknown codes
                language_name = code
        except KeyError:
            language_name = code

        as_language_enum = convert_language_to_language_enum(language_name)
        # Count the occurrence
        language_counts[as_language_enum] = language_counts.get(as_language_enum, 0) + 1
    
    return(language_counts)

def filter_low_count_entries(dic: dict[any, float], pct_min: float = 0, count_min: float = 0) -> dict[any, float]:
    """Filter low values from a dict

    Args:
        dic (dict[str, float]): The dict to filter
        pct_min (float, optional): The percent of the sum of all values each value must be over or equal to. Defaults to 0.
        count_min (float, optional): The count that values each value must be over or equal to. Defaults to 0.

    Returns:
        dict[str, float]: The filtered dict
    """
    assert(not (pct_min and count_min))
    # No count min minimum cuz it makes sense
    assert(pct_min > 0)
    
    dictCopy = dic.copy()

    filteredKeys = []
    total = 0
    # Calc total
    if(pct_min):
        for val in dictCopy.values():
            total += val

    for key, val in dictCopy.items():
        if((pct_min) and (val / total * 100 < pct_min)):
            filteredKeys.append(key)
        elif((count_min) and (val < count_min)):
            filteredKeys.append(key)
    # Delete the key if the value is of a low count
    for key in filteredKeys:
        del dictCopy[key]
    
    return(dictCopy)

def obj_array_to_obj(obj_array: list[dict[str, any]], key: str) -> dict[str, dict[str, any]]:
    """Convert an object array to an (embedded) object

    Args:
        obj_array (list[dict[str, any]]): The object array
        key (str): A unique key which is in every object in the array

    Returns:
        dict[str, dict[str, any]]: key: entry for entry in obj_array
    """
    oa      = obj_array.copy()
    new_obj = {}

    for elem in oa:
        new_obj[elem[key]] = elem
    
    return(new_obj)