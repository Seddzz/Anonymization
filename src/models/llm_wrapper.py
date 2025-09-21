"""
LLM wrapper for abstracting different language model providers.
"""

import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LLMWrapper:
    """
    Abstraction layer for different LLM providers (OpenAI, HuggingFace, etc.)
    """
    
    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo"):
        """
        Initialize LLM wrapper.
        
        Args:
            provider: LLM provider ("openai", "huggingface", "anthropic")
            model: Model name/identifier
        """
        self.provider = provider
        self.model = model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                logger.error("OpenAI package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
        elif self.provider == "huggingface":
            try:
                from transformers import pipeline
                self.client = pipeline("text-generation", model=self.model)
            except ImportError:
                logger.error("Transformers package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize HuggingFace client: {e}")
    
    def generate_text(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text or None if failed
        """
        if not self.client:
            logger.error("LLM client not initialized")
            return None
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            
            elif self.provider == "huggingface":
                response = self.client(prompt, max_length=max_tokens, temperature=temperature)
                return response[0]['generated_text']
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if the LLM is available and properly configured."""
        return self.client is not None