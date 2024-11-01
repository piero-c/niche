// models/RequestsCache.js
const mongoose = require( 'mongoose' );
const BaseSchema = require( './BaseSchema' );

const ExcludedSchema = new mongoose.Schema( {
  mbid:            { type: String, required: true },
  reason_excluded: { type: String },
  date_excluded:   { type: Date, default: Date.now },
} );

const RequestsCacheSchema = new mongoose.Schema( {
  params: {
    language:    String,
    genre:       String,
    niche_level: String,
  },
  excluded: [ ExcludedSchema ],
} );

RequestsCacheSchema.add( BaseSchema );

module.exports = mongoose.model( 'RequestsCache', RequestsCacheSchema );
