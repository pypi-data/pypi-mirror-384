#!/usr/bin/env python3
"""
Script to vectorize DI formats from di_formats.json and store them in MongoDB.
Each format becomes one document with all existing fields plus a vector field.
"""

import json
import os
import sys
from typing import List, Dict, Any
from pymongo import MongoClient
import logging
from src.config import Config
from src.embeddings import Embeddings

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def load_di_formats() -> Dict[str, Any]:
    """Load the DI formats from the JSON file."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    json_path = os.path.join(project_root, "edu_configs", "di_formats.json")
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"DI formats file not found at {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_text_for_vectorization(format_data: Dict[str, Any]) -> str:
    """Extract text from format for vectorization."""
    text_parts = []
    
    # Add grade information first
    if format_data.get('assigned_grade') is not None:
        text_parts.append(f"Grade: {format_data['assigned_grade']}")
        # Also store as 'grade' field for consistency
        format_data['grade'] = format_data['assigned_grade']
    
    # Add title
    if format_data.get('title'):
        text_parts.append(f"Title: {format_data['title']}")
    
    # Add description if available
    if format_data.get('description'):
        text_parts.append(f"Description: {format_data['description']}")
    
    # Extract teacher actions from all parts
    if format_data.get('parts'):
        for part in format_data['parts']:
            # Add part name
            if part.get('part_name'):
                text_parts.append(f"Part: {part['part_name']}")
            
            # Add part description
            if part.get('description'):
                text_parts.append(f"Part Description: {part['description']}")
            
            # Add all teacher actions from steps
            if part.get('steps'):
                for step in part['steps']:
                    if step.get('teacher_action'):
                        text_parts.append(f"Teacher Action: {step['teacher_action']}")
    
    return "\n".join(text_parts)


def setup_mongodb() -> MongoClient:
    """Setup MongoDB connection."""
    # Get MongoDB URI from environment or use default
    mongodb_uri = Config.MONGODB_URI
    client = MongoClient(mongodb_uri)
    
    # Test connection
    try:
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def create_vector_index(collection):
    """Create vector search index for the collection."""
    try:
        # Check if index already exists
        indexes = list(collection.list_indexes())
        vector_index_exists = any(index.get('name') == 'di_formats_vector_index' for index in indexes)
        
        if not vector_index_exists:
            # Create vector search index
            index_definition = {
                "fields": [
                    {
                        "type": "vector",
                        "path": "vector",
                        "numDimensions": 3072, 
                        "similarity": "cosine"
                    }
                ]
            }
            
            collection.create_search_index(
                model={
                    "definition": index_definition,
                    "name": "di_formats_vector_index"
                }
            )
            logger.info("Created vector search index")
        else:
            logger.info("Vector search index already exists")
            
    except Exception as e:
        logger.warning(f"Could not create vector index (may need Atlas): {e}")

def vectorize_and_store_formats():
    """Main function to vectorize DI formats and store in MongoDB."""
    logger.info("Starting DI formats vectorization...")
    
    # Load DI formats
    logger.info("Loading DI formats from JSON...")
    di_data = load_di_formats()
    
    # Setup clients
    embeddings = Embeddings()
    mongo_client = setup_mongodb()
    
    # Get database and collection
    db = mongo_client['chatter']  # Use existing database
    collection = db['di_formats']
    
    # Don't clear existing data to avoid duplicates
    logger.info("Checking for existing documents to avoid duplicates...")
    
    total_formats = 0
    processed_formats = 0
    
    # Process each skill
    for skill_name, skill_data in di_data.get('skills', {}).items():
        logger.info(f"Processing skill: {skill_name}")
        
        formats = skill_data.get('formats', [])
        total_formats += len(formats)
        
        for format_data in formats:
            try:
                # Extract text for vectorization
                text_content = extract_text_for_vectorization(format_data)
                
                if not text_content.strip():
                    logger.warning(f"No text content found for format {format_data.get('format_number', 'unknown')}")
                    continue
                
                # Get embedding
                vector = embeddings.get_gemini_embedding(text_content)
                
                # Create document with all existing fields plus vector
                document = {
                    **format_data,  # Include all existing fields
                    'skill_name': skill_name,  # Add skill name for context
                    'vector': vector,  # Add vector field
                    'text_content': text_content,  # Store text for debugging
                    'vectorized_at': datetime.now().isoformat()
                }
                
                # Use upsert to update if exists, insert if not
                format_number = format_data.get('format_number', 'unknown')
                collection.replace_one(
                    {'skill_name': skill_name, 'format_number': format_number},
                    document,
                    upsert=True
                )
                processed_formats += 1
                
                logger.info(f"Processed format {format_number} from {skill_name}")
                
            except Exception as e:
                logger.error(f"Error processing format {format_data.get('format_number', 'unknown')}: {e}")
                continue
    
    # Create vector index after inserting documents
    if processed_formats > 0:
        logger.info("Creating vector search index...")
        create_vector_index(collection)
    
    # Close connections
    mongo_client.close()
    
    logger.info(f"Vectorization complete!")
    logger.info(f"Total formats found: {total_formats}")
    logger.info(f"Successfully processed: {processed_formats}")
    logger.info(f"Collection: chatter.di_formats")

if __name__ == "__main__":
    from datetime import datetime
    
    try:
        vectorize_and_store_formats()
        print("\n✅ DI formats vectorization completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)