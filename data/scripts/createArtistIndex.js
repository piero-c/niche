/**
 * createIndex.js
 *
 * Creates an index on the 'genres.name' field in the 'niche.artists' collection.
 *
 * Usage:
 *   node createIndex.js
 *
 * Example:
 *   node createIndex.js
 */

const { MongoClient } = require( 'mongodb' );
const dotenv          = require( 'dotenv' );
const { exit }        = require( 'process' );

// Load environment variables from .env file (optional)
dotenv.config();

// MongoDB connection URI
const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017';

// Database and Collection Names
const dbName         = 'niche';
const collectionName = 'artists';
const indexOn        = 'genres.name';

// Function to create index
async function createIndex() {
  const client = new MongoClient( uri, { useNewUrlParser: true, useUnifiedTopology: true } );

  try {
    // Connect to MongoDB
    await client.connect();
    console.log( 'Connected to MongoDB.' );

    const db         = client.db( dbName );
    const collection = db.collection( collectionName );

    console.log( `Creating Index for ${indexOn}` );
    // Create index on
    const indexName = await collection.createIndex( { [ indexOn ]: 1 } );
    console.log( `Index created: ${indexName}` );
  } catch( error ) {
    console.error( `Error creating index: ${error.message}` );
    exit( 1 );
  } finally {
    // Close the connection
    await client.close();
    console.log( 'MongoDB connection closed.' );
  }
}

// Entry point
( async () => {
  await createIndex();
} )();
