/**
 * removeEmptyGenres.js
 *
 * Iterates over the 'artists' collection and removes entries with 0 'genres' using the MongoDB native driver.
 *
 * Usage:
 *   node removeEmptyGenres.js
 *
 * Example:
 *   node removeEmptyGenres.js
 */

const connectToDatabase = require( './db' ); // Adjust the path as necessary

// Function to remove entries with 0 'genres'
async function removeEmptyGenres() {
  let client;
  try {
    // Connect to the database
    client = await connectToDatabase();
    const db = client.db(); // Uses the default database from the URI

    // Get the 'artists' collection
    const artistCollection = db.collection( 'artists' );

    // Create an index on 'genres.name' (if not already created)
    // Note: Index creation can be handled separately if needed
    await artistCollection.createIndex( { 'genres.name': 1 } );

    // Define the query to find documents with empty or missing 'genres'
    const query = {
      $or: [
        { genres: { $exists: false } },
        { genres: { $size: 0 } },
      ],
    };

    // Count the number of documents matching the query
    const count = await artistCollection.countDocuments( query );
    console.log( `Found ${count} documents with empty or missing 'genres'.` );

    if( count > 0 ) {
      // Remove the documents
      const result = await artistCollection.deleteMany( query );
      console.log( `Removed ${result.deletedCount} documents with empty or missing 'genres'.` );
    } else {
      console.log( 'No documents to remove.' );
    }
  } catch( error ) {
    console.error( `Error removing documents: ${error.message}` );
    process.exit( 1 );
  } finally {
    // Close the connection
    if( client ) {
      await client.close();
      console.log( 'MongoDB connection closed.' );
    }
  }
}

// Entry point
( async () => {
  await removeEmptyGenres();
} )();
