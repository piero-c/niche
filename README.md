# niche

### June 16, 2025: An Update

Unfortunately, I have to discontinue this project due to <a href='https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api'>Changes in Spotify's APIs</a>

The last working status of the code included fully functional backend services. An example playlist can be found <a href='https://open.spotify.com/playlist/0wMvC89Os3fgydpX9pLfsK'> on my Spotify account </a>

The main service (create playlist), worked as follows:
- Authenticate user
- Collect artists in genre from MusicBrainz database
- Search for and validate artist on lastfm
- Get artist top tracks on spotify
- Validate track and artist once more
- Add to playlist
- If playlist is undersized after some time, use spotify recommendations \<deprecated> & custom logic to extend playlist
- Add a cover image, and return the URL

_(So, as you can see, I was already jumping through hoops to get this thing working. I'm proud of how far it has come from just an idea)_

Services:

- Get top genres
- Add more songs with Custom AI Recommendations
- Create playlist (adjust genre, year made, language, artist 'niche level', min and max song length
- Access playlists
- Filter generated playlists by all parameters, get average artist follower count for all or one generated playlist

Fully functional database creation, seeding, and maintenence scripts were also written.

My plan was to create a React/TypeScript frontend, and get this thing hosted on GCP for people to enjoy for free. What a shame.

Thank you for reading. Let's encourage healthy competition in all industries to facilitate broader access to high quality options, especially for building cool stuff like this!

Piero
