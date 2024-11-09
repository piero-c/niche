import os
import time
import pycountry

from dotenv import load_dotenv
from enum   import Enum
from bidict import bidict

NICHE_APP_URL = 'http://niche-app.net'

MIN_SONGS_FOR_PLAYLIST_GEN = 4

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
        "MB_CLIENT_ID"       : os.getenv("MB_CLIENT_ID"),
        "MB_CLIENT_SECRET"   : os.getenv("MB_CLIENT_SECRET")
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

def convert_s_to_ms(s: int) -> int:
    """Convert s to ms

    Args:
        s (int): s

    Returns:
        int: ms
    """
    return(s * 1000)

def strcomp(*strings: str) -> bool:
    """Return true if all strings are equal case-insensitive

    Returns:
        bool: Are they equal?
    """
    first = strings[0].strip().lower()
    return(all(s.strip().lower() == first for s in strings))

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

def map_language_codes(language_codes: list[str], iso639_type: int = 3) -> dict[Language, int]:
    """
    Maps ISO 639 language codes to full language names and counts occurrences.

    Args:
        language_codes: A list of language codes.
        iso639_type: The iso 639 type. Defaults to 3. Must be 1 or 3

    Returns:
        A dictionary where keys are language names and values are counts.
    """
    language_counts: dict[str, int] = {}
    for code in language_codes:
        try:
            if(iso639_type == 3):
                language = pycountry.languages.get(alpha_3=code)
            else:
                language = pycountry.languages.get(alpha_2=code)
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
    assert((not pct_min) or (pct_min > 0))
    
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


def scale_from_highest(d: dict[str, float], maxx: int) -> dict:
    """Scale a dictionary of numbers, based on the scalar which multiplies the highest value in the dict to get it to max. Then sort in descending order

    Args:
        d (dict[str, float]): The dict
        maxx (int): Highest val will be set to this

    Returns:
        dict: sorted and scaled
    """
    d_copy = d.copy()

    d_copy = dict(sorted(d_copy.items(), key=lambda item: item[1], reverse=True))

    max_value = list(d_copy.values())[0]

    scaler = maxx / max_value

    for k in d_copy.keys():
        d_copy[k] = round(d_copy[k] * scaler, 2)
    
    return(d_copy)