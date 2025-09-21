"""Tests for the agent module."""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from agent.executor import AnonymizerPipeline


class TestAgent(unittest.TestCase):
    """Test cases for the agent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = AnonymizerPipeline()
    
    def test_pipeline_initialization(self):
        """Test that the pipeline initializes correctly."""
        self.assertIsNotNone(self.pipeline)
        self.assertIsNotNone(self.pipeline.spacy_detector)
        self.assertIsNotNone(self.pipeline.faker_replacer)
    
    def test_text_anonymization(self):
        """Test basic text anonymization."""
        test_text = "Hello, my name is John Doe and I live in New York."
        result = self.pipeline.anonymize_text(test_text)
        
        # Check that we get a result
        self.assertIsNotNone(result)
        self.assertIn('anonymized_text', result)
        self.assertIn('entities_found', result)


if __name__ == '__main__':
    unittest.main()