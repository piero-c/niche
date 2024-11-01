// models/BaseSchema.js
const mongoose = require( 'mongoose' );
const config = require( '../config.json' );

const ENV = process.env.NODE_ENV;
if( !ENV ) {
  throw new Error( "Please specify an environment" );
}
const cfg = config[ ENV ];

const BaseSchema = new mongoose.Schema( {}, { timestamps: true } );

BaseSchema.add( new mongoose.Schema( {
  created_by: { type: String, default: cfg.user },
  updated_by: { type: String, default: cfg.user },
} ) );

module.exports = BaseSchema;
