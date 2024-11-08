import os
import json
import re
import unicodedata
from pathlib import Path

def normalize_word(word):
    """Normalize word to be case-insensitive, ignore hyphens/spaces, and remove accents for comparison only."""
    word = unicodedata.normalize('NFD', word)  # Decompose accented characters
    word = ''.join(char for char in word if unicodedata.category(char) != 'Mn')  # Remove accents
    return re.sub(r"[-\s]", "", word.strip().lower())

def find_common_words(master_file_path, other_files):
    """Find the common genres (not considering case or hyphens or accents)"""
    # Load master file words without modifying the actual words
    with open(master_file_path, 'r') as master_file:
        master_words = {normalize_word(word): word.strip() for word in master_file}

    # Initialize dictionaries for collecting matches and partial matches
    common_words_dict = {}
    unmatched_master_words = set(master_words.keys())  # Track unmatched words
    partial_matches = []  # To store words found in only some files

    # Compare each other file with the master file
    for file_path in other_files:
        file_name = os.path.basename(file_path)
        
        # Load words from the current file, preserving original word
        with open(file_path, 'r') as other_file:
            other_words = {normalize_word(word): word.strip() for word in other_file}

        # Find common normalized words between master and current file
        for normalized, master_word in master_words.items():
            if normalized in other_words:
                # Initialize entry if not present
                if normalized not in common_words_dict:
                    common_words_dict[normalized] = {os.path.basename(master_file_path): master_word}
                # Add the original word from the current file to the entry
                common_words_dict[normalized][file_name] = other_words[normalized]
                # Remove matched word from unmatched set
                unmatched_master_words.discard(normalized)

    # Prepare unmatched list if words are not in ALL files
    for normalized, master_word in master_words.items():
        if normalized in common_words_dict:
            matched_files = common_words_dict[normalized].keys()
            missing_files = [os.path.basename(file) for file in other_files if os.path.basename(file) not in matched_files]
            
            # If the word is not present in all files, add it to partial_matches
            if missing_files:
                partial_entry = {os.path.basename(master_file_path): master_word}
                for missing_file in missing_files:
                    partial_entry[missing_file] = ""
                partial_matches.append(partial_entry)

    # Prepare the final common_words list for JSON output
    common_words = list(common_words_dict.values())
    unmatched_words = [master_words[normalized] for normalized in unmatched_master_words]

    return common_words, unmatched_words, partial_matches

def save_to_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def save_unmatched_words(unmatched_words, output_path):
    """Save unmatched words to a separate file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        for word in unmatched_words:
            file.write(word + '\n')

def save_partial_matches(partial_matches, output_path):
    """Save partial matches to a separate file in JSON format."""
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(partial_matches, file, ensure_ascii=False, indent=4)

# Main function
def main(master_file_path, data_dir):
    # List of all files in data directory, excluding the master file
    other_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f != os.path.basename(master_file_path) and os.path.isfile(os.path.join(data_dir, f))]

    # Find common words, unmatched words, and partial matches
    common_words, unmatched_words, partial_matches = find_common_words(master_file_path, other_files)

    # Save common words to JSON file
    json_output_path = Path('scripts/genres/data/master/genres.json')
    save_to_json(common_words, json_output_path)
    print(f"Data saved to {json_output_path}")

    # Save unmatched words to `not-covered.txt` in master folder
    unmatched_output_path = Path('scripts/genres/data/master/not-covered.txt')
    save_unmatched_words(unmatched_words, unmatched_output_path)
    print(f"Unmatched words saved to {unmatched_output_path}")

    # Save partial matches to `unmatched.txt` in master folder
    partial_matches_output_path = Path('scripts/genres/data/master/unmatched.txt')
    save_partial_matches(partial_matches, partial_matches_output_path)
    print(f"Partial matches saved to {partial_matches_output_path}")

# Example usage
master_file_path = Path('scripts/genres/data/SPOTIFY')  # Adjust path to the master file
data_dir = Path('scripts/genres/data')  # Directory where other files are stored
main(master_file_path, data_dir)
