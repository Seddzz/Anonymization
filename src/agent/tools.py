"""
Consolidate all anonymization tools
"""

# Import existing detectors
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .tools.detectors.llm_detector import LLMDetector  
from .tools.detectors.spacy_detector import SpacyDetector
from .tools.replacers.faker_replacer import FakerReplacer

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
