# Genre Handling

### Description:
  Handle valid genres and different genre names across services
  Get user's top genres from spotify

### Entry:
    valid_genres.py
      Call genres() to get valid genres for requests
        Returns a list of valid genres
      
      get_genre_dict_list() and convert_genre() is used for other functions to use and is not for the client

    top_genres.py
    Get user's top genres from spotify
    Call the do() function
        Returns the top genres as a GenreInterestCount

### Features to Implement:
    TODO Give the user genre recommendations based on their favourite genres  TODO (bleh probably add as a feature that will never be added -- would probably have to use open api or whatever ml slop nlp schtuff) - but still can get their top genres as like motivation or whatever make them do the work
