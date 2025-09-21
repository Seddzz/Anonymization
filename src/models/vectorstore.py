"""
Vector store management for semantic search and storage.
"""

import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector storage and retrieval for semantic operations.
    """
    
    def __init__(self, store_path: str = "data/vectorstore"):
        """
        Initialize vector store.
        
        Args:
            store_path: Path to store vector data
        """
        self.store_path = store_path
        self.vectors = {}
        self.metadata = {}
        self.embeddings_manager = None
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize the vector store."""
        os.makedirs(self.store_path, exist_ok=True)
        
        # Try to load existing embeddings manager
        try:
            from .embeddings import EmbeddingsManager
            self.embeddings_manager = EmbeddingsManager()
        except ImportError:
            logger.warning("Embeddings manager not available")
        
        # Load existing vectors if available
        self._load_store()
    
    def _load_store(self):
        """Load existing vectors from disk."""
        vectors_file = os.path.join(self.store_path, "vectors.pkl")
        metadata_file = os.path.join(self.store_path, "metadata.pkl")
        
        try:
            if os.path.exists(vectors_file):
                with open(vectors_file, 'rb') as f:
                    self.vectors = pickle.load(f)
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                    
            logger.info(f"Loaded {len(self.vectors)} vectors from store")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
    
    def _save_store(self):
        """Save vectors to disk."""
        vectors_file = os.path.join(self.store_path, "vectors.pkl")
        metadata_file = os.path.join(self.store_path, "metadata.pkl")
        
        try:
            with open(vectors_file, 'wb') as f:
                pickle.dump(self.vectors, f)
            
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            logger.info(f"Saved {len(self.vectors)} vectors to store")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
        """
        if not self.embeddings_manager:
            logger.error("Embeddings manager not available")
            return
        
        try:
            # Generate embeddings
            embeddings = self.embeddings_manager.encode(documents)
            
            if embeddings is None:
                logger.error("Failed to generate embeddings")
                return
            
            # Store vectors and metadata
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                doc_id = f"doc_{len(self.vectors)}"
                self.vectors[doc_id] = embedding
                
                doc_metadata = {"text": doc}
                if metadata and i < len(metadata):
                    doc_metadata.update(metadata[i])
                
                self.metadata[doc_id] = doc_metadata
            
            # Save to disk
            self._save_store()
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of (doc_id, similarity_score, metadata) tuples
        """
        if not self.embeddings_manager or not self.vectors:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_manager.encode([query])[0]
            
            # Calculate similarities
            similarities = []
            for doc_id, doc_embedding in self.vectors.items():
                similarity = self.embeddings_manager.similarity(query_embedding, doc_embedding)
                similarities.append((doc_id, similarity, self.metadata.get(doc_id, {})))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        return self.metadata.get(doc_id)
    
    def clear(self):
        """Clear all vectors and metadata."""
        self.vectors.clear()
        self.metadata.clear()
        self._save_store()