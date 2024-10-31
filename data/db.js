// db.js
const mongoose = require( 'mongoose' );
const dotenv = require( 'dotenv' );

dotenv.config();

const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/niche';

mongoose.connect( uri );

const db = mongoose.connection;

db.on( 'error', console.error.bind( console, 'MongoDB connection error:' ) );
db.once( 'open', () => {
  console.log( 'Connected to MongoDB.' );
} );

module.exports = mongoose;
