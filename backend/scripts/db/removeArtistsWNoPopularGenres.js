const fs = require( 'fs' );
const path = require( 'path' );
const connectToDatabase = require( './db' ); // Adjust path if db.js is in a different directory

async function removeArtistsWNoPopularGenres() {
  // Load genres.json
  const genresFilePath = path.join( __dirname, '..', 'genres', 'data', 'master', 'genres.json' );
  const genresData = JSON.parse( fs.readFileSync( genresFilePath, 'utf-8' ) );

  // Extract MUSICBRAINZ genres and remove duplicates
  const musicbrainzGenres = Array.from( new Set(
    genresData
      .map( entry => entry.MUSICBRAINZ )
      .filter( genre => genre ), // Remove any undefined or null entries
  ) );

  // Connect to the database
  const client = await connectToDatabase();
  const db = client.db(); // Assumes default database, modify if necessary
  const artistsCollection = db.collection( 'artists' );

  try {
    // Build a filter to match artists where none of the genres match any in `musicbrainzGenres`
    const filter = {
      'genres.name': { $nin: musicbrainzGenres },
    };

    // Perform the deletion
    const result = await artistsCollection.deleteMany( filter );

    console.log( `${result.deletedCount} artists without MUSICBRAINZ genres removed.` );
  } catch( error ) {
    console.error( 'Error removing entries:', error );
  } finally {
    // Close the database connection
    await client.close();
  }
}

// Run the script
removeArtistsWNoPopularGenres().catch( console.error );
