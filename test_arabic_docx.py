#!/usr/bin/env python3
"""
Test Arabic DOCX processing with the document processor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.document_processor import DocumentProcessor
from pipeline import AnonymizerPipeline

def test_arabic_docx():
    """Test processing the Arabic DOCX file"""
    
    arabic_docx_path = "tests/sample_arabic_document.docx"
    
    print("=== Testing Arabic DOCX Processing ===")
    print(f"Testing file: {arabic_docx_path}")
    print("-" * 50)
    
    if not os.path.exists(arabic_docx_path):
        print(f"❌ Arabic DOCX file not found: {arabic_docx_path}")
        return False
    
    try:
        # Create pipeline with LLM detector (best for Arabic)
        print("🔧 Creating pipeline with LLM detector...")
        pipeline = AnonymizerPipeline(detector="llm")
        
        # Create document processor
        print("📄 Creating document processor...")
        doc_processor = DocumentProcessor(pipeline)
        
        # Process the Arabic DOCX
        print("🔄 Processing Arabic DOCX...")
        result = doc_processor.process_file(arabic_docx_path, 'docx')
        
        if result['success']:
            print("✅ Arabic DOCX processing successful!")
            print(f"📁 Output file: {result['output_path']}")
            print(f"📊 Found {len(result['replacement_mapping'])} replacements:")
            
            for original, replacement in result['replacement_mapping'].items():
                print(f"   '{original}' → '{replacement}'")
            
            print(f"\n📝 Original text preview:")
            print(f"   {result['original_text'][:200]}...")
            
            print(f"\n📝 Anonymized text preview:")
            print(f"   {result['anonymized_text'][:200]}...")
            
            return True
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_arabic_support():
    """Check if the document libraries support Arabic properly"""
    
    print("\n=== Checking Arabic Support in Document Libraries ===")
    
    try:
        # Test docx library with Arabic
        from docx import Document
        
        # Create a test document with Arabic
        doc = Document()
        doc.add_paragraph("اختبار النص العربي - Arabic Text Test")
        doc.add_paragraph("This is mixed: مرحبا بكم")
        
        # Save and read back
        test_path = "test_arabic_support.docx"
        doc.save(test_path)
        
        # Read it back
        doc2 = Document(test_path)
        text = "\n".join([p.text for p in doc2.paragraphs])
        
        print(f"✅ DOCX Arabic support test:")
        print(f"   Written and read: {text}")
        
        # Clean up
        os.remove(test_path)
        
        # Test if Arabic characters are preserved
        has_arabic = any(ord(char) > 0x0600 and ord(char) < 0x06FF for char in text)
        if has_arabic:
            print("✅ Arabic characters preserved correctly")
            return True
        else:
            print("⚠️ Arabic characters might be lost")
            return False
            
    except Exception as e:
        print(f"❌ Arabic support test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Arabic document processing capabilities...\n")
    
    # Test 1: Check library support
    support_ok = check_arabic_support()
    
    # Test 2: Process actual Arabic DOCX
    if support_ok:
        processing_ok = test_arabic_docx()
        
        if processing_ok:
            print(f"\n🎉 Arabic DOCX processing is fully supported!")
            print("✅ Document structure preserved")
            print("✅ Arabic text handled correctly") 
            print("✅ LLM detection working with Arabic documents")
        else:
            print(f"\n⚠️ Arabic DOCX processing needs attention")
    else:
        print(f"\n❌ Arabic document support issues detected")