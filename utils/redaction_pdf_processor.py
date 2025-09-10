"""
Alternative PDF processor that uses redaction-based text replacement
for more reliable text removal and replacement.
"""

import fitz  # PyMuPDF for advanced PDF manipulation
import os
from typing import Dict, List, Tuple, Any


class RedactionBasedPDFProcessor:
    """
    PDF processor that uses redaction annotations for complete text removal
    """
    
    def __init__(self, pipeline):
        """
        Initialize with anonymization pipeline
        
        Args:
            pipeline: The anonymization pipeline with detector and replacer
        """
        self.pipeline = pipeline
        
    def anonymize_pdf_with_redaction(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """
        Anonymize PDF using redaction-based approach for complete text removal
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF (optional)
            
        Returns:
            Dictionary with processing results
        """
        try:
            if output_path is None:
                output_path = input_path.replace('.pdf', '_anonymized.pdf')
            
            # Open the PDF document
            doc = fitz.open(input_path)
            
            # Extract text for anonymization mapping
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            
            # Get anonymization mappings
            anonymized_text = self.pipeline.anonymize(full_text)
            replacement_details = self.pipeline.replacer.get_replacements_with_types()
            
            # Build replacement mapping (sort by length for better matching)
            replacement_mapping = {}
            for original, replacement, entity_type in replacement_details:
                replacement_mapping[original] = replacement
            
            print(f"📝 Processing PDF with {len(replacement_mapping)} replacements")
            
            # Process each page
            total_replacements = 0
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_replacements = 0
                
                print(f"\n📄 Processing page {page_num + 1}")
                
                # For each replacement, find and redact all instances
                for original_text, replacement_text in sorted(replacement_mapping.items(), key=lambda x: len(x[0]), reverse=True):
                    if len(original_text.strip()) < 2:  # Skip very short strings
                        continue
                        
                    # Search for text instances on the page
                    text_instances = page.search_for(original_text)
                    
                    for inst in text_instances:
                        print(f"🎯 Found '{original_text}' at {inst}")
                        
                        # Get the text's formatting from the area
                        text_dict = page.get_text("dict", clip=inst)
                        
                        # Extract formatting from the text
                        font_info = self._extract_font_info(text_dict)
                        
                        if font_info:
                            font = font_info.get('font', 'helv')
                            size = font_info.get('size', 12)
                            color = font_info.get('color', (0, 0, 0))
                        else:
                            # Default formatting
                            font = 'helv'
                            size = 12
                            color = (0, 0, 0)
                        
                        # Add redaction annotation to completely remove original text
                        redact_annot = page.add_redact_annot(inst, fill=(1, 1, 1))
                        
                        # Apply redaction to completely erase the text
                        page.apply_redactions()
                        
                        # Insert replacement text with preserved formatting
                        result = page.insert_text(
                            (inst.x0, inst.y1 - 2),  # Position
                            replacement_text,
                            fontsize=size,
                            fontname=font,
                            color=color
                        )
                        
                        if result >= 0:
                            print(f"✅ Successfully replaced '{original_text}' with '{replacement_text}'")
                            page_replacements += 1
                        else:
                            print(f"⚠️ Failed to insert replacement text")
                
                print(f"✅ Page {page_num + 1}: {page_replacements} replacements")
                total_replacements += page_replacements
            
            print(f"\n🎉 Total replacements made: {total_replacements}")
            
            # Save the anonymized PDF
            doc.save(output_path)
            doc.close()
            
            return {
                'success': True,
                'output_path': output_path,
                'original_text': full_text,
                'anonymized_text': anonymized_text,
                'replacement_mapping': replacement_mapping,
                'replacements_made': total_replacements,
                'message': f'PDF anonymized using redaction method: {os.path.basename(output_path)} ({total_replacements} replacements)',
                'file_type': 'pdf'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error in redaction-based PDF processing: {str(e)}',
                'file_type': 'pdf'
            }
    
    def _extract_font_info(self, text_dict: dict) -> dict:
        """
        Extract font information from text dictionary
        
        Args:
            text_dict: Text dictionary from PyMuPDF
            
        Returns:
            Dictionary with font information
        """
        try:
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span.get("text", "").strip():
                                return {
                                    'font': span.get('font', 'helv'),
                                    'size': span.get('size', 12),
                                    'color': self._convert_color(span.get('color', 0)),
                                    'flags': span.get('flags', 0)
                                }
        except Exception:
            pass
        
        return None
    
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
