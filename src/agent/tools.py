"""
Tools used by the agent for anonymization tasks.
"""

import sys
import os
from typing import List, Dict, Any
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .tools.detectors.llm_detector import LLMDetector  
from .tools.detectors.spacy_detector import SpacyDetector
from .tools.replacers.faker_replacer import FakerReplacer


class DetectorTool:
    """Tool for entity detection."""
    
    def __init__(self, detector_type: str = 'spacy'):
        """Initialize detector tool."""
        self.detector_type = detector_type
        if detector_type == 'llm':
            self.detector = LLMDetector()
        else:
            self.detector = SpacyDetector()
    
    def detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """Detect entities in text."""
        return self.detector.detect_entities(text)


class ReplacerTool:
    """Tool for entity replacement."""
    
    def __init__(self, replacer_type: str = 'faker'):
        """Initialize replacer tool."""
        self.replacer_type = replacer_type
        self.replacer = FakerReplacer()
    
    def replace_entities(self, text: str, entities: List[Dict[str, Any]]) -> str:
        """Replace entities in text."""
        return self.replacer.replace_entities(text, entities)


class AnonymizationTools:
    """Collection of tools for anonymization"""
    
    def __init__(self):
        self.detectors = {
            'llm': LLMDetector(),
            'spacy': SpacyDetector()
        }
        self.replacers = {
            'faker': FakerReplacer()
        }
    
    def get_detector(self, detector_type):
        """Get a specific detector"""
        return self.detectors.get(detector_type)
    
    def get_replacer(self, replacer_type):
        """Get a specific replacer"""
        return self.replacers.get(replacer_type)
