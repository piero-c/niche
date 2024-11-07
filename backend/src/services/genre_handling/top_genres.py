from src.auth.SpotifyUser import SpotifyUser
def do():
    user = SpotifyUser()
    return(user.get_top_genres())

if __name__ == '__main__':
    do()