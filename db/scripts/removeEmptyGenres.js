/**
 * removeEmptyGenres.js
 *
 * Iterates over the 'niche.artists' collection and removes entries with 0 'genres' using Mongoose and db.js.
 *
 * Usage:
 *   node removeEmptyGenres.js
 *
 * Example:
 *   node removeEmptyGenres.js
 */

const dotenv = require( 'dotenv' );
const mongoose = require( '../db' ); // Adjust the path as necessary

// Load environment variables from .env file (optional)
dotenv.config();

// Define the Artist model (assuming it hasn't been defined elsewhere)
const ArtistSchema = new mongoose.Schema( {}, { strict: false } );

// Create an index on 'genres.name' (if not already created)
// Note: Index creation can be handled separately if needed
ArtistSchema.index( { 'genres.name': 1 } );

// Create the Artist model
const Artist = mongoose.model( 'Artist', ArtistSchema, 'artists' );

// Function to remove entries with 0 'genres'
async function removeEmptyGenres() {
  try {
    // Ensure the connection is established
    if( mongoose.connection.readyState !== 1 ) {
      await mongoose.connection;
      console.log( 'Connected to MongoDB.' );
    }

    // Define the query to find documents with empty or missing 'genres'
    const query = {
      $or: [
        { genres: { $exists: false } },
        { genres: { $size: 0 } },
      ],
    };

    // Count the number of documents matching the query
    const count = await Artist.countDocuments( query );
    console.log( `Found ${count} documents with empty or missing 'genres'.` );

    if( count > 0 ) {
      // Remove the documents
      const result = await Artist.deleteMany( query );
      console.log( `Removed ${result.deletedCount} documents with empty or missing 'genres'.` );
    } else {
      console.log( 'No documents to remove.' );
    }
  } catch( error ) {
    console.error( `Error removing documents: ${error.message}` );
    process.exit( 1 );
  } finally {
    // Close the connection
    await mongoose.connection.close();
    console.log( 'MongoDB connection closed.' );
  }
}

// Entry point
( async () => {
  await removeEmptyGenres();
} )();
