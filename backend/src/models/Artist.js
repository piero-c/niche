// models/Artist.js
const mongoose = require( 'mongoose' );

// Define a schema with strict mode set to false to allow any fields
const ArtistSchema = new mongoose.Schema( {}, { strict: false } );

// Add an index on 'genres.name'
ArtistSchema.index( { 'genres.name': 1 } );

// Create and export the model
module.exports = mongoose.model( 'Artist', ArtistSchema, 'artists' );
