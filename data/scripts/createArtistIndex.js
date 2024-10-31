// scripts/createArtistIndex.js
const mongoose = require( '../db' );
const Artist = require( '../models/Artist' );

( async () => {
  try {
    // Wait for the connection to be established
    await mongoose.connection;

    // Create the index
    await Artist.createIndexes();
    console.log( 'Index on genres.name created.' );
  } catch( error ) {
    console.error( 'Error creating index:', error.message );
  } finally {
    // Close the connection
    mongoose.connection.close();
  }
} )();
