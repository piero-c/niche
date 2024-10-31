// models/Request.js
const mongoose = require( 'mongoose' );
const BaseSchema = require( './BaseSchema' );

const RequestSchema = new mongoose.Schema( {
  user:   { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  params: {
    songs_min_year_created: Number,
    songs_length_min_secs:  Number,
    songs_length_max_secs:  Number,
    language:               String,
    genre:                  String,
    lastfm_listeners_max:   Number,
    lastfm_listeners_min:   Number,
    lastfm_playcount_max:   Number,
    lastfm_playcount_min:   Number,
    spotify_followers_max:  Number,
    spotify_followers_min:  Number,
    niche_level:            String,
    lastfm_likeness_min:    Number,
    playlist_length:        Number,
  },
  playlist_generated: { type: mongoose.Schema.Types.ObjectId, ref: 'Playlist' },
} );

RequestSchema.add( BaseSchema );

module.exports = mongoose.model( 'Request', RequestSchema );
