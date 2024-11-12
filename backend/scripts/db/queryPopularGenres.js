const fs = require( 'fs' );
const path = require( 'path' );
const connectToDatabase = require( './db' ); // Adjust the path if db.js is in a different directory

async function queryPopularGenres() {
  // Load genres.json
  const genresJsonFilePath = path.join( __dirname, '..', 'genres', 'data', 'master', 'genres.json' );
  const genresJsonData = JSON.parse( fs.readFileSync( genresJsonFilePath, 'utf-8' ) );

  // Create a set of existing genres from genres.json for quick lookup
  const existingGenresSet = new Set(
    genresJsonData
      .map( entry => entry.MUSICBRAINZ )
      .filter( genre => genre ), // Remove any undefined or null entries
  );

  // Read genres from the MUSICBRAINZ file
  const musicbrainzFilePath = path.join( __dirname, '..', 'genres', 'data', 'MUSICBRAINZ' );
  const genresToCheck = fs.readFileSync( musicbrainzFilePath, 'utf-8' )
    .split( '\n' )
    .map( line => line.trim() )
    .filter( line => line.length > 0 ); // Remove empty lines

  // Connect to the database
  const client = await connectToDatabase();
  const db = client.db(); // Use the default database, modify if necessary
  const artistsCollection = db.collection( 'artists' );

  const genresToWrite = [];

  try {
    // Iterate over each genre from the MUSICBRAINZ file
    for( const genre of genresToCheck ) {
      // Check if the genre is not already in genres.json
      if( !existingGenresSet.has( genre ) ) {
        // Query the database for the count of documents matching the genre
        const count = await artistsCollection.countDocuments( { 'genres.name': genre } );

        if( count > 200 ) {
          genresToWrite.push( genre );
          console.log( `Genre "${genre}" has ${count} entries.` );
        }
      }
    }
  } catch( error ) {
    console.error( 'Error querying the database:', error );
  } finally {
    // Close the database connection
    await client.close();
  }

  // Write the popular genres to popular_genres.txt
  const outputFilePath = path.join( __dirname, '..', 'genres', 'data', 'master', 'popular_genres.txt' );
  fs.writeFileSync( outputFilePath, genresToWrite.join( '\n' ), 'utf-8' );
  console.log( `Popular genres written to ${outputFilePath}` );
}

// Run the script
queryPopularGenres().catch( console.error );
