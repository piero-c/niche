// models/BaseSchema.js
const mongoose = require( 'mongoose' );

const BaseSchema = new mongoose.Schema( {}, { timestamps: true } );

BaseSchema.add( {
  created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  updated_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
} );

module.exports = BaseSchema;
