from auth.SpotifyUser import SpotifyUser
def get():
    user = SpotifyUser()
    return(user.get_top_genres())