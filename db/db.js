// db.js
const mongoose = require( 'mongoose' );
const config = require( './config.json' );

const ENV = process.env.NODE_ENV;
if( !ENV ) {
  throw new Error( "Please specify an environment" );
}
const cfg = config[ ENV ];

const uri = cfg.MONGODB_URI || 'mongodb://localhost:27017/niche';

mongoose.connect( uri );

const db = mongoose.connection;

db.on( 'error', console.error.bind( console, 'MongoDB connection error:' ) );
db.once( 'open', () => {
  console.log( 'Connected to MongoDB.' );
} );

module.exports = mongoose;
