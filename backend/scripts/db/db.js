// db.js
const { MongoClient } = require( 'mongodb' );
const dotenv = require( 'dotenv' );
const config = require( '../../config/config.json' );

dotenv.config();

const ENV = process.env.ENV;
if( !ENV ) {
  throw new Error( "Please specify an environment" );
}
const cfg = config[ ENV ];
const uri = cfg.MONGO_URI;

// Function to connect to the database
async function connectToDatabase() {
  const client = new MongoClient( uri );

  try {
    await client.connect();
    console.log( 'Connected to MongoDB.' );
    return client;
  } catch( error ) {
    console.error( 'MongoDB connection error:', error );
    throw error;
  }
}

module.exports = connectToDatabase;
