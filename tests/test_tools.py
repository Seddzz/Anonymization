"""Tests for the tools module."""

import unittest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from agent.tools import DetectorTool, ReplacerTool


class TestTools(unittest.TestCase):
    """Test cases for the tools functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector_tool = DetectorTool()
        self.replacer_tool = ReplacerTool()
    
    def test_detector_tool(self):
        """Test that the detector tool works correctly."""
        test_text = "John Doe lives in Paris."
        entities = self.detector_tool.detect_entities(test_text)
        
        # Check that we get results
        self.assertIsInstance(entities, list)
    
    def test_replacer_tool(self):
        """Test that the replacer tool works correctly."""
        entities = [{'text': 'John Doe', 'label': 'PERSON', 'start': 0, 'end': 8}]
        result = self.replacer_tool.replace_entities("John Doe lives here.", entities)
        
        # Check that replacement occurred
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, "John Doe lives here.")


if __name__ == '__main__':
    unittest.main()