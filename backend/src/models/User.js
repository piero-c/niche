// models/User.js
const mongoose = require( 'mongoose' );
const BaseSchema = require( './BaseSchema' );

const UserSchema = new mongoose.Schema( {
  display_name: { type: String, required: true },
  spotify_id:   { type: String, required: true },
} );

UserSchema.add( BaseSchema );

module.exports = mongoose.model( 'User', UserSchema );
