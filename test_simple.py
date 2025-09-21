import sys
import os
from utils.document_processor import DocumentProcessor
from pipeline import AnonymizerPipeline

def test_arabic_docx():
    arabic_docx_path = "tests/sample_arabic_document.docx"
    
    print("Testing Arabic DOCX Processing...")
    print(f"Testing file: {arabic_docx_path}")
    
    if not os.path.exists(arabic_docx_path):
        print(f"ERROR: Arabic DOCX file not found")
        return False
    
    try:
        # Create pipeline with LLM detector
        print("Creating pipeline...")
        pipeline = AnonymizerPipeline(detector="llm")
        
        # Create document processor
        print("Creating document processor...")
        doc_processor = DocumentProcessor(pipeline)
        
        # Process the Arabic DOCX
        print("Processing Arabic DOCX...")
        result = doc_processor.process_file(arabic_docx_path, 'docx')
        
        if result['success']:
            print("SUCCESS: Arabic DOCX processing worked!")
            print(f"Output file: {result['output_path']}")
            print(f"Found {len(result['replacement_mapping'])} replacements")
            
            print("\nReplacements found:")
            for original, replacement in result['replacement_mapping'].items():
                print(f"  '{original}' -> '{replacement}'")
            
            return True
        else:
            print(f"ERROR: Processing failed - {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_arabic_docx()