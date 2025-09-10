"""
Advanced PDF processor that preserves formatting, fonts, colors, and layout
while anonymizing sensitive information.
"""

import fitz  # PyMuPDF for advanced PDF manipulation
import os
from typing import Dict, List, Tuple, Any
import re
from .redaction_pdf_processor import RedactionBasedPDFProcessor


class AdvancedPDFProcessor:
    """
    Advanced PDF processor that maintains original formatting while anonymizing text
    """
    
    def __init__(self, pipeline):
        """
        Initialize with anonymization pipeline
        
        Args:
            pipeline: The anonymization pipeline with detector and replacer
        """
        self.pipeline = pipeline
        self.replacement_mapping = {}
        self.redaction_processor = RedactionBasedPDFProcessor(pipeline)
        
    def anonymize_pdf_with_formatting(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Anonymize PDF while preserving all formatting, fonts, colors, and layout
        Uses redaction-based approach for more reliable text replacement
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF (optional)
            
        Returns:
            Dictionary with processing results
        """
        try:
            print("🚀 Starting advanced PDF anonymization with redaction method...")
            
            # Use the redaction-based processor for more reliable text replacement
            result = self.redaction_processor.anonymize_pdf_with_redaction(input_path, output_path)
            
            if result['success']:
                result['message'] += " (Advanced formatting preservation with complete text redaction)"
            
            return result
            
        except Exception as e:
            print(f"❌ Advanced PDF processing failed: {str(e)}")
            return {
                'success': False,
                'error': f'Error in advanced PDF processing: {str(e)}',
                'file_type': 'pdf'
            }
    
    def _convert_color(self, color_int: int) -> Tuple[float, float, float]:
        """
        Convert PyMuPDF color integer to RGB tuple
        
        Args:
            color_int: Color as integer
            
        Returns:
            RGB tuple (values between 0 and 1)
        """
        if color_int == 0:
            return (0, 0, 0)  # Black
        
        # Convert integer to RGB
        r = ((color_int >> 16) & 255) / 255.0
        g = ((color_int >> 8) & 255) / 255.0
        b = (color_int & 255) / 255.0
        
        return (r, g, b)
    
    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        """
        Extract text with complete formatting information
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text elements with formatting details
        """
        try:
            doc = fitz.open(pdf_path)
            formatted_text = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_dict = page.get_text("dict")
                
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                formatted_text.append({
                                    'page': page_num + 1,
                                    'text': span["text"],
                                    'bbox': span["bbox"],
                                    'font': span.get("font", ""),
                                    'size': span.get("size", 12),
                                    'flags': span.get("flags", 0),
                                    'color': span.get("color", 0)
                                })
            
            doc.close()
            return formatted_text
            
        except Exception as e:
            print(f"Error extracting formatted text: {e}")
            return []


class FormattingPreservedDocumentProcessor:
    """
    Enhanced document processor that uses advanced formatting preservation
    """
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.advanced_pdf = AdvancedPDFProcessor(pipeline)
    
    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process file with advanced formatting preservation
        """
        if file_type is None:
            file_type = file_path.split('.')[-1].lower()
        
        if file_type == 'pdf':
            try:
                # Try advanced PDF processing first
                result = self.advanced_pdf.anonymize_pdf_with_formatting(file_path)
                
                if result['success']:
                    return result
                else:
                    print(f"⚠️ Advanced PDF processing failed: {result.get('error', 'Unknown error')}")
                    print("🔄 Falling back to basic PDF processing...")
                    
                    # Fallback to basic processing
                    from .document_processor import DocumentProcessor
                    basic_processor = DocumentProcessor(self.pipeline)
                    fallback_result = basic_processor.process_file(file_path, file_type)
                    
                    # Add a note about the fallback
                    if fallback_result['success']:
                        fallback_result['message'] += " (Advanced formatting preservation failed, using basic processing)"
                    
                    return fallback_result
                    
            except Exception as e:
                print(f"⚠️ Advanced PDF processing error: {str(e)}")
                print("🔄 Falling back to basic PDF processing...")
                
                # Fallback to basic processing
                from .document_processor import DocumentProcessor
                basic_processor = DocumentProcessor(self.pipeline)
                fallback_result = basic_processor.process_file(file_path, file_type)
                
                # Add a note about the fallback
                if fallback_result['success']:
                    fallback_result['message'] += " (Advanced formatting preservation failed, using basic processing)"
                
                return fallback_result
        else:
            # For non-PDF files, fall back to basic processing
            from .document_processor import DocumentProcessor
            basic_processor = DocumentProcessor(self.pipeline)
            return basic_processor.process_file(file_path, file_type) 
