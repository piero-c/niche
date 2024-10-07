# USAGE - python3 -m scripts.spotify_genre.spotify_top_genres

from scripts.spotify_genre.SpotifyUser import SpotifyUser

def main() -> dict[str, int|float]:
    user = SpotifyUser()
    print(user.get_top_genres())


if __name__ == "__main__":
    main()