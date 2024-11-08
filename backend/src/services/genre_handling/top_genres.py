from src.auth.SpotifyUser import spotify_user

from config.personal_init import token

def do():
    user = spotify_user
    user.initialize(token)
    return(user.get_top_genres())

if __name__ == '__main__':
    print(do())