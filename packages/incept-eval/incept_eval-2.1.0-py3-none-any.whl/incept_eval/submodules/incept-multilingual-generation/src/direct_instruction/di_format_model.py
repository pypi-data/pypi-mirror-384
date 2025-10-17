"""
DiFormatModel for vector search of DI formats in MongoDB.
"""

import logging
from typing import List, Dict, Optional
from src.config import Config
from src.embeddings import Embeddings
from src.utils.vector_store import get_mongodb_client

logger = logging.getLogger(__name__)


class DiFormatModel:
    """Handles vector search operations for DI formats in MongoDB."""

    def __init__(self):
        """Initialize MongoDB connection and embeddings."""
        self.embeddings = Embeddings()
        self.mongo_client = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection using shared pooled client."""
        try:
            self.mongo_client = get_mongodb_client()
            # Test connection
            self.mongo_client.admin.command('ping')
            
            db = self.mongo_client['chatter']
            self.collection = db['di_formats']
            
            logger.info("Successfully connected to MongoDB di_formats collection")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def vector_search_formats(self, query: str, limit: int = 5, grade: Optional[int] = None, skill_name: Optional[str] = None) -> List[Dict]:
        """
        Search DI formats using vector similarity with fallback to grade/skill filtering.
        
        Args:
            query: The search query text
            limit: Maximum number of results to return
            grade: Optional grade filter
            skill_name: Optional skill name filter
            
        Returns:
            List of matching format documents with similarity scores
        """
        try:
            
            # Get query embedding using Gemini
            query_vector = self.embeddings.get_gemini_embedding(query)
            
            # Build vector search stage with optional filters
            vector_search_stage = {
                "index": "di_formats_vector_index",
                "path": "vector",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit
            }
            
            # Add filters within vectorSearch if specified
            filter_conditions = {}
            if grade is not None:
                filter_conditions["grade"] = {"$eq": grade}
            if skill_name is not None:
                filter_conditions["skill_name"] = {"$eq": skill_name}
            
            if filter_conditions:
                vector_search_stage["filter"] = filter_conditions
            
            # Build aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": vector_search_stage
                },
                {
                    "$project": {
                        "_id": 1,
                        "skill_name": 1,
                        "format_number": 1,
                        "title": 1,
                        "grade": 1,
                        "parts": 1,
                        "text_content": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            logger.info(f"Vector search found {len(results)} results")
            
            # If no results from vector search, fall back to grade/skill filtering
            if not results and (grade is not None or skill_name is not None):
                logger.info(f"No vector search results, falling back to grade/skill filtering")
                
                fallback_filter = {}
                if grade is not None:
                    fallback_filter["grade"] = grade
                if skill_name is not None:
                    fallback_filter["skill_name"] = skill_name

                logger.info(f"Fallback filter: {fallback_filter}")
                
                fallback_results = list(self.collection.find(
                    fallback_filter,
                    {
                        "_id": 1,
                        "skill_name": 1,
                        "format_number": 1,
                        "title": 1,
                        "grade": 1,
                        "parts": 1,
                        "text_content": 1
                    }
                ).limit(limit))
                
                # Add a default score for fallback results
                for result in fallback_results:
                    result["score"] = 0.7  # Moderate confidence for exact matches
                
                logger.info(f"Fallback search found {len(fallback_results)} results")
                return fallback_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def close(self):
        """Close MongoDB connection (no-op for shared pooled client)."""
        # Don't close the shared singleton client - it's managed at app level
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (no-op for shared pooled client)."""
        # Don't close the shared client - it needs to stay open for concurrent requests
        pass