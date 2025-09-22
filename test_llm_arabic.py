#!/usr/bin/env python3
"""
Test script for LLM entity detection with Arabic text
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.tools.detectors.llm_detector import LLMDetector

def test_arabic_detection():
    """Test LLM detection with Arabic text"""
    print("🚀 Testing LLM Entity Detection with Arabic Text")
    print("=" * 50)
    
    # Initialize the LLM detector
    detector = LLMDetector(model="mistral")
    
    # Arabic test text with personal information
    arabic_text = """اسمي أحمد محمد وأعمل في شركة جوجل في الرياض. عمري 30 سنة ورقم هاتفي 0501234567. بريدي الإلكتروني ahmad.mohammed@gmail.com أسكن في حي الملز في الرياض."""
    
    print("📝 Testing Arabic Text:")
    print(f"   {arabic_text.strip()}")
    print()
    
    # Test entity detection
    print("🔍 Running LLM entity detection...")
    entities = detector.detect(arabic_text)
    
    print(f"\n✅ Detection Results:")
    print(f"   Found {len(entities)} entities")
    print()
    
    if entities:
        for i, entity in enumerate(entities, 1):
            print(f"   {i}. Text: '{entity[0]}'")
            print(f"      Type: {entity[1]}")
            print(f"      Position: {entity[2]}-{entity[3]}")
            print()
    else:
        print("   ⚠️ No entities detected")
    
    return entities

def test_english_detection():
    """Test LLM detection with English text for comparison"""
    print("\n" + "=" * 50)
    print("🔄 Testing with English text for comparison")
    print("=" * 50)
    
    detector = LLMDetector(model="mistral")
    
    english_text = """
    My name is John Smith and I work at Google in New York.
    I am 30 years old and my phone number is +1-555-123-4567.
    My email is john.smith@gmail.com
    I live in Manhattan, New York.
    """
    
    print("📝 Testing English Text:")
    print(f"   {english_text.strip()}")
    print()
    
    print("🔍 Running LLM entity detection...")
    entities = detector.detect(english_text)
    
    print(f"\n✅ Detection Results:")
    print(f"   Found {len(entities)} entities")
    print()
    
    if entities:
        for i, entity in enumerate(entities, 1):
            print(f"   {i}. Text: '{entity[0]}'")
            print(f"      Type: {entity[1]}")
            print(f"      Position: {entity[2]}-{entity[3]}")
            print()
    else:
        print("   ⚠️ No entities detected")
    
    return entities

if __name__ == "__main__":
    print("🤖 LLM Arabic Entity Detection Test")
    print("Using Mistral via Ollama")
    print()
    
    try:
        # Test Arabic detection
        arabic_results = test_arabic_detection()
        
        # Test English for comparison
        english_results = test_english_detection()
        
        print("\n" + "=" * 50)
        print("📊 Summary")
        print("=" * 50)
        print(f"Arabic entities detected: {len(arabic_results)}")
        print(f"English entities detected: {len(english_results)}")
        
        if arabic_results:
            print("✅ Arabic detection working!")
        else:
            print("⚠️ Arabic detection needs improvement")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()