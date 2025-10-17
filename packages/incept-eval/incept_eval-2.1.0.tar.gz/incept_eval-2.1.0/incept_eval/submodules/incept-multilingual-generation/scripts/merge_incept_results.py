#!/usr/bin/env python3
"""
Merge imagen_incept.json results into main imagen.json file
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

def merge_incept_results():
    """Merge incept results from imagen_incept.json into main imagen.json"""
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    main_json_path = os.path.join(project_root, "data", "imagen.json")
    incept_json_path = os.path.join(project_root, "data", "imagen_incept.json")
    
    # Load both files
    try:
        # Load main imagen.json
        with open(main_json_path, 'r') as f:
            main_data = json.load(f)
        logger.info(f"Loaded {len(main_data)} entries from main imagen.json")
    except FileNotFoundError:
        logger.error("Main imagen.json not found")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error reading main imagen.json: {e}")
        return
        
    try:
        # Load imagen_incept.json
        with open(incept_json_path, 'r') as f:
            incept_data = json.load(f)
        logger.info(f"Loaded {len(incept_data)} entries from imagen_incept.json")
    except FileNotFoundError:
        logger.error("imagen_incept.json not found")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error reading imagen_incept.json: {e}")
        return
    
    # Create a mapping of questions to incept data
    incept_map = {entry['question']: entry['incept_v1'] for entry in incept_data if 'question' in entry and 'incept_v1' in entry}
    
    # Statistics
    updated_entries = 0
    new_entries = 0
    
    # Update main data with incept results
    for i, entry in enumerate(main_data):
        if 'question' in entry and entry['question'] in incept_map:
            # Add incept_v1 data to existing entry
            main_data[i]['incept_v1'] = incept_map[entry['question']]
            updated_entries += 1
            logger.info(f"Updated entry: {entry['question'][:50]}...")
    
    # Find questions in incept data that don't exist in main data
    main_questions = {entry['question'] for entry in main_data if 'question' in entry}
    
    for incept_entry in incept_data:
        if incept_entry['question'] not in main_questions:
            # Create new entry in main data
            new_entry = {
                'question': incept_entry['question'],
                'grade': incept_entry['grade'],
                'topic': incept_entry['topic'],
                'incept_v1': incept_entry['incept_v1']
            }
            main_data.append(new_entry)
            new_entries += 1
            logger.info(f"Created new entry: {incept_entry['question'][:50]}...")
    
    # Write updated data back to main file
    try:
        with open(main_json_path, 'w') as f:
            json.dump(main_data, f, indent=2)
        logger.info(f"Successfully updated main imagen.json")
        print(f"✅ Merge completed:")
        print(f"   - Updated {updated_entries} existing entries with incept_v1 data")
        print(f"   - Added {new_entries} new entries")
        print(f"   - Total entries in imagen.json: {len(main_data)}")
    except Exception as e:
        logger.error(f"Error writing to main imagen.json: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    merge_incept_results()