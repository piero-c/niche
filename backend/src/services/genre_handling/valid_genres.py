from pathlib import Path
from typing  import TypedDict

import json

# Specify the path to your JSON file
file_path = Path('src/services/genre_handling/genres.json')

service_genre_names    = 'SPOTIFY'
service_secondary_name = 'MUSICBRAINZ'

class GenreDict(TypedDict):
    SPOTIFY    : str
    MUSICBRAINZ: str
    LASTFM     : str

def genre_is_spotify(genre: str) -> bool:
    data = get_genre_dict_list()
    entry = next((item for item in data if item.get('SPOTIFY', '') == genre), None)
    if(entry):
        return(True)
    return(False)

def convert_genre(from_service: str, to_service: str, genre: str) -> str:
    """Convert genre name from one service to another

    Args:
        from_service (str): Must be one of SPOTIFY, MUSICBRAINZ, LASTFM
        to_service (str): Must be one of SPOTIFY, MUSICBRAINZ, LASTFM
        genre (str): The genre as named in the from_service
    Returns:
        str: The genre as named in the to_service
    """
    assert((from_service == 'MUSICBRAINZ') or (from_service == 'SPOTIFY') or (from_service == 'LASTFM'))
    assert((to_service == 'MUSICBRAINZ') or (to_service == 'SPOTIFY') or (to_service == 'LASTFM'))
    data = get_genre_dict_list()
    entry = next((item for item in data if item.get(from_service, '') == genre), None)
    if(entry):
        return(entry[to_service])

def get_genre_dict_list() -> list[GenreDict]:
    """Get the list of dicts of genres

    Returns:
        list[GenreDict]: the list of dicts of genres
    """
    with open(file_path, 'r') as file:
        data: list[GenreDict] = json.load(file)
    
    return(data)

def genres() -> list[str]:
    """Get valid genres (spotify genre seed format)

    Returns:
        list[str]: List of genres
    """
    genre_list = []
    data = get_genre_dict_list()
    
    for genre in data:
        genre_list.append(genre.get(service_genre_names) or genre.get(service_secondary_name))
    
    return (genre_list)

if __name__ == '__main__':
    print(genres())

