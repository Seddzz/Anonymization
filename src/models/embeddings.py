"""
Embeddings management for vector operations.
"""

import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Handles text embeddings for vector operations.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embeddings manager.
        
        Args:
            model_name: Name of the embedding model
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock embeddings")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for input texts.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Embeddings array or None if failed
        """
        if not self.model:
            # Return mock embeddings if model not available
            return np.random.random((len(texts), 384))
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score
        """
        try:
            # Normalize embeddings
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(norm1, norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def is_available(self) -> bool:
        """Check if embeddings model is available."""
        return self.model is not None