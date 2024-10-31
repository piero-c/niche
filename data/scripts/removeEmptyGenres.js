/**
 * removeEmptyGenres.js
 *
 * Iterates over the 'niche.artists' collection and removes entries with 0 'genres'.
 *
 * Usage:
 *   node removeEmptyGenres.js
 *
 * Example:
 *   node removeEmptyGenres.js
 */

const { MongoClient } = require( 'mongodb' );
const dotenv = require( 'dotenv' );
const { exit } = require( 'process' );

// Load environment variables from .env file (optional)
dotenv.config();

// MongoDB connection URI
const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017';

// Database and Collection Names
const dbName = 'niche';
const collectionName = 'artists';

// Function to remove entries with 0 'genres'
async function removeEmptyGenres() {
  const client = new MongoClient( uri, { useNewUrlParser: true, useUnifiedTopology: true } );

  try {
    // Connect to MongoDB
    await client.connect();
    console.log( 'Connected to MongoDB.' );

    const db = client.db( dbName );
    const collection = db.collection( collectionName );

    // Define the query to find documents with empty or missing 'genres'
    const query = {
      $or: [
        { genres: { $exists: false } },
        { genres: { $size: 0 } },
      ],
    };

    // Count the number of documents matching the query
    const count = await collection.countDocuments( query );
    console.log( `Found ${count} documents with empty or missing 'genres'.` );

    if( count > 0 ) {
      // Remove the documents
      const result = await collection.deleteMany( query );
      console.log( `Removed ${result.deletedCount} documents with empty or missing 'genres'.` );
    } else {
      console.log( 'No documents to remove.' );
    }
  } catch( error ) {
    console.error( `Error removing documents: ${error.message}` );
    exit( 1 );
  } finally {
    // Close the connection
    await client.close();
    console.log( 'MongoDB connection closed.' );
  }
}

// Entry point
( async () => {
  await removeEmptyGenres();
} )();
