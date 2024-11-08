from src.auth.SpotifyUser import spotify_user

def do():
    user = spotify_user
    return(user.get_top_genres())

if __name__ == '__main__':
    do()