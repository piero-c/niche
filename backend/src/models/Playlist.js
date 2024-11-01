// models/Playlist.js
const mongoose = require( 'mongoose' );
const BaseSchema = require( './BaseSchema' );

const PlaylistSchema = new mongoose.Schema( {
  user:    { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  name:    { type: String, required: true },
  request: { type: mongoose.Schema.Types.ObjectId, ref: 'Request' },
  link:    { type: String },
} );

PlaylistSchema.add( BaseSchema );

module.exports = mongoose.model( 'Playlist', PlaylistSchema );
