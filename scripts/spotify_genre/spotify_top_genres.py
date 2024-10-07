from SpotifyUser import SpotifyUser

def main() -> dict[str, int|float]:
    user = SpotifyUser()
    print(user.get_top_genres())


if __name__ == "__main__":
    main()