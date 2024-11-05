# Playlist Editor

### Description:
    Allow the user to further customize their playlist

### Entry:


TODO - update length db if artists added (no)

    
### Features to Implement:
   - Button to try different niche level if the request doesnt generate enough songs (delete the playlist) or just keep it (frontend)

    - Option to add more songs by an artist - get valid songs fn then add song fn
    - Option to add more songs from spotify recommendations -- 
```
1. **Retrieve Tracks from a Playlist**:
   - Use the endpoint `GET /v1/playlists/{playlist_id}/tracks` to get a list of tracks from a playlist.
   - Extract the `seed` information from this list, typically by using the track IDs, artist IDs, or genre data from these tracks.

2. **Use the Recommendations Endpoint**:
   - Once you have the seeds, you can use `GET /v1/recommendations` to get recommendations based on those seeds.
   - This endpoint allows you to specify up to five seed values across `seed_artists`, `seed_tracks`, or `seed_genres`.
   - You can also adjust parameters such as target `popularity`, `energy`, `danceability`, and other audio features to fine-tune the recommendations.

### Example Workflow

1. **Extract Seed Data**:
   - Choose a few tracks from the playlist to use as `seed_tracks` or their artists as `seed_artists`.

2. **Fetch Recommendations**:
   - Call the `GET /v1/recommendations` endpoint with the selected seeds.

### Example Request for Recommendations

```http
GET https://api.spotify.com/v1/recommendations?seed_tracks=4NHQUGzhtTLFvgF5SZesLK&limit=10
Authorization: Bearer {access_token}
```

This would return a list of recommended tracks based on the seed track specified.

### Considerations

- **Limitations on Seed Tracks**: You can only provide up to five seeds in a single request.
- **Fine-Tuning**: Spotify’s API allows you to refine recommendations by providing min, max, or target values for various audio features (e.g., `danceability`, `energy`).
- **Dynamic Recommendations**: Since recommendations are generated dynamically, the response may vary over time or based on regional popularity.

By combining playlist tracks with the recommendations endpoint, you can generate playlist-inspired song recommendations effectively.

(would only check for spotify followers, song length, and stuff like that, assume the rest applies)
```