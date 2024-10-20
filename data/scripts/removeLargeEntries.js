#!/usr/bin/env node

/**
 * removeLargeEntries.js
 *
 * A Node.js script to filter out oversized JSONL documents from a file.
 *
 * Usage:
 *   node removeLargeEntries.js --input <input_file> --output <output_file> --max_size_mb <size_in_MB>
 *
 * Example:
 *   node removeLargeEntries.js -i ~/Desktop/niche/data/artists.jsonl -o ~/Desktop/niche/data/artists_filtered.jsonl -m 15
 */

const fs = require( 'fs' );
const readline = require( 'readline' );
const path = require( 'path' );
const { exit } = require( 'process' );

// Function to display usage instructions
function showUsage() {
  const scriptName = path.basename( process.argv[ 1 ] );
  console.log( `
Usage:
  node ${scriptName} --input <input_file> --output <output_file> --max_size_mb <size_in_MB>

Options:
  --input, -i        Path to the input JSONL file. (Required)
  --output, -o       Path to the output filtered JSONL file. (Required)
  --max_size_mb, -m  Maximum allowed document size in MB. Default is 15 MB. (Optional)
  --help, -h         Show this help message.

Example:
  node ${scriptName} -i ~/Desktop/niche/data/artists.jsonl -o ~/Desktop/niche/data/artists_filtered.jsonl -m 15
    ` );
}

// Function to parse command-line arguments
function parseArgs() {
  const args = process.argv.slice( 2 );
  const argObj = {};

  for( let i = 0; i < args.length; i++ ) {
    switch( args[ i ] ) {
      case '--input':
      case '-i':
        argObj.input = args[ ++i ];
        break;
      case '--output':
      case '-o':
        argObj.output = args[ ++i ];
        break;
      case '--max_size_mb':
      case '-m':
        argObj.maxSizeMB = parseFloat( args[ ++i ] );
        // eslint-disable-next-line no-restricted-globals
        if( isNaN( argObj.maxSizeMB ) || argObj.maxSizeMB <= 0 ) {
          console.error( 'Error: --max_size_mb must be a positive number.' );
          showUsage();
          exit( 1 );
        }
        break;
      case '--help':
        break;
      case '-h':
        showUsage();
        exit( 0 );
        break;
      default:
        console.error( `Unknown argument: ${args[ i ]}` );
        showUsage();
        exit( 1 );
        break;
    }
  }

  // Validate required arguments
  if( !argObj.input || !argObj.output ) {
    console.error( 'Error: --input and --output are required.' );
    showUsage();
    exit( 1 );
  }

  // Set default maxSizeMB if not provided
  if( !argObj.maxSizeMB ) {
    argObj.maxSizeMB = 15;
  }

  return argObj;
}

// Main function to filter large documents
async function filterLargeDocuments( inputPath, outputPath, maxSizeMB ) {
  // Convert MB to bytes
  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  // Initialize counters
  let totalLines = 0;
  let removedLines = 0;
  const removedLineNumbers = [];

  // Create read and write streams
  const readStream = fs.createReadStream( inputPath, { encoding: 'utf8' } );
  const writeStream = fs.createWriteStream( outputPath, { encoding: 'utf8' } );

  // Create readline interface
  const rl = readline.createInterface( {
    input:     readStream,
    crlfDelay: Infinity,
  } );

  console.log( `\nStarting to filter documents...
Input File: ${inputPath}
Output File: ${outputPath}
Maximum Document Size: ${maxSizeMB} MB\n` );

  for await ( const line of rl ) {
    totalLines += 1;
    // Calculate byte size of the line
    const lineSize = Buffer.byteLength( line, 'utf8' );

    if( lineSize > maxSizeBytes ) {
      removedLines += 1;
      removedLineNumbers.push( totalLines );
      // Optionally, you can log the line content or other details here
    } else {
      writeStream.write( `${line}\n` );
    }

    // Optional: Display progress every 1 million lines
    if( totalLines % 1_000_000 === 0 ) {
      console.log( `Processed ${totalLines} lines...` );
    }
  }

  // Close the write stream
  writeStream.end();

  // Log the results
  console.log( `\nFiltering Complete!
Total Lines Processed: ${totalLines}
Total Lines Removed (exceeding ${maxSizeMB} MB): ${removedLines}` );

  if( removedLines > 0 ) {
    console.log( `\nLine Numbers of Removed Documents:
${removedLineNumbers.join( ', ' )}` );
  }

  console.log( '\nFiltered file has been created successfully.\n' );
}

// Entry point
( async () => {
  const args = parseArgs();
  const inputPath = args.input;
  const outputPath = args.output;
  const maxSizeMB = args.maxSizeMB;

  // Check if input file exists
  if( !fs.existsSync( inputPath ) ) {
    console.error( `Error: Input file does not exist at path '${inputPath}'.` );
    exit( 1 );
  }

  // Ensure the output directory exists
  const outputDir = path.dirname( outputPath );
  if( !fs.existsSync( outputDir ) ) {
    console.error( `Error: Output directory does not exist at path '${outputDir}'.` );
    exit( 1 );
  }

  // Start filtering
  try {
    await filterLargeDocuments( inputPath, outputPath, maxSizeMB );
  } catch( error ) {
    console.error( `An error occurred during processing: ${error.message}` );
    exit( 1 );
  }
} )();

