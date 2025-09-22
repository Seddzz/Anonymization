#!/usr/bin/env python3
"""
Quick test to verify SpaCy fallback works
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.tools.detectors.llm_detector import LLMDetector

def test_fallback():
    """Test that SpaCy fallback import works"""
    print("🧪 Testing SpaCy Fallback Import")
    print("=" * 40)
    
    detector = LLMDetector(model="mistral")
    
    # Force a fallback by calling the private method directly
    try:
        entities = detector._spacy_fallback("John Smith works at Google.")
        print(f"✅ Fallback successful! Found {len(entities)} entities")
        for entity in entities:
            print(f"   - {entity[0]} ({entity[1]})")
        return True
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fallback()
    if success:
        print("\n🎉 SpaCy fallback is working correctly!")
    else:
        print("\n❌ SpaCy fallback needs fixing")