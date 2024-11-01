// scripts/createArtistIndex.js
const connectToDatabase = require( './db' );

( async () => {
  let client;
  try {
    // Connect to the database
    client = await connectToDatabase();
    const db = client.db(); // Use the default database from the URI

    // Get the Artist collection
    const artistCollection = db.collection( 'artists' );

    // Create the index
    await artistCollection.createIndex( { 'genres.name': 1 } );
    console.log( 'Index on genres.name created.' );
  } catch( error ) {
    console.error( 'Error creating index:', error );
  } finally {
    // Close the connection
    if( client ) {
      await client.close();
    }
  }
} )();
