"""
Embeddings utility for generating vectors using Gemini or OpenAI.
"""

import logging
from typing import List
from google import genai
from openai import OpenAI

logger = logging.getLogger(__name__)


class Embeddings:
    """Handles text embedding generation using Gemini or OpenAI."""
    
    def __init__(self):
        """Initialize the clients."""
        self.gemini_client = genai.Client()
        self.openai_client = OpenAI()
    
    def get_gemini_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using Gemini.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector (3072 dimensions)
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            result = self.gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error getting Gemini embedding for text: {e}")
            raise
    
    def get_openai_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """
        Get embedding for text using OpenAI.

        Args:
            text: The text to embed
            model: OpenAI embedding model (text-embedding-3-small or text-embedding-3-large)

        Returns:
            List of floats representing the embedding vector (1536 dimensions)

        Raises:
            Exception: If embedding generation fails
        """
        try:
            response = self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding for text: {e}")
            raise