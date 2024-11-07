const fs = require( 'fs' );
const path = require( 'path' );
const connectToDatabase = require( './db' ); // Adjust path if db.js is in a different directory

async function queryPopularGenres() {
  // Load genres.json
  const genresFilePath = path.join( __dirname, '..', 'genres', 'data', 'master', 'genres.json' );
  const genresData = JSON.parse( fs.readFileSync( genresFilePath, 'utf-8' ) );

  // Extract MUSICBRAINZ genres
  const genresToQuery = genresData
    .map( entry => entry.MUSICBRAINZ )
    .filter( genre => genre ); // Remove any undefined entries

  // Connect to the database
  const client = await connectToDatabase();
  const db = client.db(); // Assumes default database, modify if necessary
  const artistsCollection = db.collection( 'artists' );

  const popularGenres = [];

  try {
    // Query each genre and count the entries
    for( const genre of genresToQuery ) {
      const count = await artistsCollection.countDocuments( { 'genres.name': genre } );

      if( count < 200 ) {
        popularGenres.push( `${genre}: ${count}` );
        console.log( `Genre "${genre}" has ${count} entries.` );
      }
    }
  } catch( error ) {
    console.error( 'Error querying database:', error );
  } finally {
    // Close the database connection
    await client.close();
  }

  // Write the popular genres to popular_genres.txt
  const outputFilePath = path.join( __dirname, '..', 'genres', 'data', 'master', 'unpopular_genres.txt' );
  fs.writeFileSync( outputFilePath, popularGenres.join( '\n' ), 'utf-8' );
  console.log( `Popular genres written to ${outputFilePath}` );
}

// Run the query
queryPopularGenres().catch( console.error );
