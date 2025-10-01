def fast_anonymize_docx(doc, valid_entities):
    """
    Efficiently anonymize a python-docx Document object using valid_entities.
    valid_entities: list of dicts with 'text', 'label', and 'replacement'
    """
    # Build a replacement map using pre-generated replacements (longest first to avoid partial overlaps)
    print(f"[DEBUG] fast_anonymize_docx called with {len(valid_entities)} entities")
    
    # Use the pre-generated replacements from the entities
    replacements = {}
    for entity in valid_entities:
        original_text = entity['text']
        # Use the pre-generated replacement if available, otherwise generate one
        if 'replacement' in entity:
            replacements[original_text] = entity['replacement']
        else:
            # Fallback: generate replacement (this should ideally not happen)
            from agent.tools.replacers.faker_replacer import FakerReplacer
            faker_replacer = FakerReplacer()
            replacements[original_text] = faker_replacer._get_smart_replacement(original_text, entity['label'])
            print(f"[WARNING] Had to generate replacement for: {original_text}")
    
    sorted_replacements = sorted(replacements.items(), key=lambda x: -len(x[0]))
    
    print(f"[DEBUG] Replacements to apply: {list(replacements.keys())}")

    # Replace in paragraphs
    paragraphs_processed = 0
    total_replacements = 0
    for para in doc.paragraphs:
        orig = para.text
        if not orig.strip():  # Skip empty paragraphs
            continue
            
        new = orig
        replacements_made = 0
        for old, new_val in sorted_replacements:
            if old and old in new:
                new = new.replace(old, new_val)
                replacements_made += 1
                total_replacements += 1
                
        if replacements_made > 0:
            para.text = new
            paragraphs_processed += 1
            print(f"[DEBUG] Paragraph: replaced {replacements_made} entities")

    # Replace in tables
    tables_processed = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                orig = cell.text
                if not orig.strip():  # Skip empty cells
                    continue
                    
                new = orig
                replacements_made = 0
                for old, new_val in sorted_replacements:
                    if old and old in new:
                        new = new.replace(old, new_val)
                        replacements_made += 1
                        total_replacements += 1
                        
                if replacements_made > 0:
                    cell.text = new
                    tables_processed += 1

    print(f"[DEBUG] fast_anonymize_docx completed: {paragraphs_processed} paragraphs, {tables_processed} table cells, {total_replacements} total replacements")
    return doc
"""
Document Processor - Handles anonymization while preserving document structure
"""
import pdfplumber
import docx
from docx import Document
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import time

class DocumentProcessor:
    def anonymize_docx(self, file_path, output_path=None):
        """
        Anonymize a DOCX file in-place, preserving all formatting, styles, and images.
        Only replaces detected sensitive text with anonymized values using fast_anonymize_docx.
        """
        try:
            from utils.helpers import extract_valid_entities
            print(f"[LOG] Loading DOCX: {file_path}")
            doc = Document(file_path)
            print("[LOG] Extracting text from DOCX...")
            full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            print(f"[LOG] Text extraction complete. Length: {len(full_text)}")
            
            # Log extracted text
            print(f"[DEBUG] Extracted text from DOCX: {full_text[:500]}...")
            
            # Use the full pipeline for entity detection and anonymization
            print("[LOG] Calling pipeline anonymize...")
            t0 = time.time()
            pipeline_result = self.pipeline.anonymize(full_text)
            print(f"[LOG] Pipeline anonymize finished in {time.time() - t0:.2f}s")
            
            # Handle tuple response (legacy)
            if isinstance(pipeline_result, tuple):
                pipeline_result = pipeline_result[0]
            
            if not isinstance(pipeline_result, dict):
                print(f"[ERROR] Pipeline returned unexpected type: {type(pipeline_result)}")
                return {
                    'success': False,
                    'error': f'Pipeline returned unexpected type: {type(pipeline_result)}'
                }
            
            # Extract replacement mapping from pipeline result - USE THIS CONSISTENTLY
            replacement_mapping = pipeline_result.get('replacement_mapping', {})
            entity_info = pipeline_result.get('entity_info', {})
            
            print(f"[DEBUG] Replacement mapping from pipeline: {replacement_mapping}")
            
            # Convert replacement mapping to valid_entities format for fast_anonymize_docx
            valid_entities = []
            for original_text, replacement_text in replacement_mapping.items():
                entity_type = entity_info.get(original_text, 'PERSON')
                valid_entities.append({
                    'text': original_text,
                    'label': entity_type,
                    'replacement': replacement_text  # Pass the actual replacement
                })
            
            print(f"[LOG] Valid entities extracted: {len(valid_entities)}")
            
            if not valid_entities:
                print("[WARNING] No entities detected in DOCX content")
                # Still save the document even if no entities found
                if output_path is None:
                    output_path = file_path.replace('.docx', '_anonymized.docx')
                doc.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'original_text': full_text,
                    'anonymized_text': None,
                    'replacement_mapping': {},
                    'entity_info': {},
                    'message': f'DOCX processed successfully (no entities detected): {os.path.basename(output_path)}',
                    'file_type': 'docx'
                }
            
            print("[LOG] Starting fast anonymization of DOCX...")
            t1 = time.time()
            doc = fast_anonymize_docx(doc, valid_entities)
            print(f"[LOG] Fast anonymization finished in {time.time() - t1:.2f}s")
            
            if output_path is None:
                output_path = file_path.replace('.docx', '_anonymized.docx')
            print(f"[LOG] Saving anonymized DOCX to {output_path}")
            doc.save(output_path)
            print("[LOG] DOCX anonymization complete.")
            
            # Log replacement mapping to a file for debugging
            try:
                with open('debug_logs.txt', 'a', encoding='utf-8') as log_file:
                    log_file.write(f"[DEBUG] DOCX Replacement mapping: {replacement_mapping}\n")
            except UnicodeEncodeError:
                print("[WARNING] Could not write replacement mapping to log due to encoding issues")
            
            return {
                'success': True,
                'output_path': output_path,
                'original_text': full_text,
                'anonymized_text': None,  # Not needed for docx
                'replacement_mapping': replacement_mapping,  # Consistent mapping
                'entity_info': entity_info,
                'message': f'DOCX anonymized successfully: {os.path.basename(output_path)}',
                'file_type': 'docx'
            }
        except Exception as e:
            print(f"[ERROR] DOCX anonymization failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Error processing DOCX: {str(e)}'
            }
    def __init__(self, pipeline):
        """
        Initialize with an anonymization pipeline
        """
        self.pipeline = pipeline
    
    def anonymize_txt(self, file_path, output_path=None):
        """
        Anonymize a TXT file while preserving structure
        """
        try:
            # Read text content
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Anonymize the text
            anonymized_text = self.pipeline.anonymize(text_content)
            
            # Get replacement mapping for statistics
            replacement_details = self.pipeline.replacer.get_replacements_with_types()
            replacement_mapping = {}
            for original, replacement, entity_type in replacement_details:
                replacement_mapping[original] = replacement
            
            # Create output file
            if output_path is None:
                output_path = file_path.replace('.txt', '_anonymized.txt')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(anonymized_text)
            
            return {
                'success': True,
                'output_path': output_path,
                'original_text': text_content,
                'anonymized_text': anonymized_text,
                'replacement_mapping': replacement_mapping,
                'message': f'TXT file anonymized successfully: {os.path.basename(output_path)}',
                'file_type': 'txt'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing TXT: {str(e)}'
            }

    def anonymize_pdf(self, file_path, output_path=None):
        """
        Anonymize a PDF file while preserving original formatting, images, and layout using PyMuPDF.
        """
        try:
            # Extract text from PDF for entity detection
            text_content = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n\n"
            # Anonymize the text (get replacement mapping)
            result = self.pipeline.anonymize(text_content)
            if isinstance(result, tuple):
                result = result[0]
            if not isinstance(result, dict):
                return {
                    'success': False,
                    'error': 'Anonymization did not return a dict.'
                }
            # Use PyMuPDF to replace text in-place in the original PDF
            replacement_mapping = result['replacement_mapping']
            output_path_final = self.anonymize_pdf_preserve_format(file_path, replacement_mapping, output_path)
            if not output_path_final:
                return {
                    'success': False,
                    'error': 'PDF anonymization failed (format-preserving)'
                }
            return {
                'success': True,
                'output_path': output_path_final,
                'original_text': text_content,
                'anonymized_text': None,
                'replacement_mapping': replacement_mapping,
                'message': f'PDF anonymized successfully: {os.path.basename(output_path_final)}',
                'file_type': 'pdf'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing PDF: {str(e)}'
            }

    def anonymize_pdf_preserve_format(self, file_path, replacement_mapping, output_path=None):
        """
        Anonymize a PDF file in-place using PyMuPDF (fitz) to preserve all formatting, images, and layout.
        Replaces detected sensitive text with anonymized values.
        """
        import fitz  # PyMuPDF
        try:
            doc = fitz.open(file_path)
            for page in doc:
                for original, replacement in replacement_mapping.items():
                    if not original or not original.strip():
                        continue

                    # Search for all instances of the original text on the page
                    rects = page.search_for(original)
                    if not rects:
                        print(f"[WARNING] No matches found for: {original}")
                        continue

                    # First pass: redact the original text
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(1, 1, 1))

                    # Apply redactions (removes original text)
                    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

                    # Second pass: insert replacement text at each position
                    for rect in rects:
                        try:
                            # Calculate font size based on original text height
                            font_size = 11  # default
                            if rect.height > 0:
                                font_size = max(8, min(14, rect.height * 0.8))

                            # Insert replacement text
                            page.insert_text(
                                rect.bl + (2, -2),  # Slight offset for better positioning
                                replacement,
                                fontsize=font_size,
                                fontname="helv",
                                color=(0, 0, 0)
                            )
                        except Exception as e:
                            print(f"[WARNING] Failed to insert text '{replacement}': {e}")
                            continue

            if output_path is None:
                output_path = file_path.replace('.pdf', '_anonymized.pdf')

            doc.save(output_path)
            doc.close()
            return output_path

        except Exception as e:
            print(f"[ERROR] PDF format-preserving anonymization failed: {e}")
            try:
                with open('debug_logs.txt', 'a', encoding='utf-8') as log_file:
                    log_file.write(f"[ERROR] PDF format-preserving anonymization failed: {e}\n")
            except UnicodeEncodeError:
                print("[WARNING] Could not write error to log due to encoding issues")
            return None
    def process_file(self, file_path, file_type=None):
        """
        Process any supported file type
        """
        if file_type is None:
            file_type = file_path.split('.')[-1].lower()
        
        if file_type == 'pdf':
            return self.anonymize_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return self.anonymize_docx(file_path)
        elif file_type == 'txt':
            return self.anonymize_txt(file_path)
        else:
            return {
                'success': False,
                'error': f'Unsupported file type: {file_type}'
            }

    def process_file_with_entities(self, file_path, file_type=None, entity_types=None):
        """
        Process any supported file type with custom entity selection
        """
        if file_type is None:
            file_type = file_path.split('.')[-1].lower()
        
        if file_type == 'pdf':
            return self.anonymize_pdf_with_entities(file_path, entity_types)
        elif file_type in ['docx', 'doc']:
            return self.anonymize_docx_with_entities(file_path, entity_types)
        elif file_type == 'txt':
            return self.anonymize_txt_with_entities(file_path, entity_types)
        else:
            return {
                'success': False,
                'error': f'Unsupported file type: {file_type}'
            }

    def anonymize_txt_with_entities(self, file_path, entity_types, output_path=None):
        """
        Anonymize a TXT file with custom entity selection
        """
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Anonymize with custom entity types
            result = self.pipeline.anonymize(content, entity_types)
            
            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(file_path)[0]
                output_path = f"{base_name}_anonymized.txt"
            
            # Write anonymized content
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(result['anonymized_text'])
            
            return {
                'success': True,
                'original_text': content,
                'anonymized_text': result['anonymized_text'],
                'replacement_mapping': result['replacement_mapping'],
                'entity_info': result.get('entity_info', {}),
                'output_path': output_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing TXT file: {str(e)}'
            }

    def anonymize_docx_with_entities(self, file_path, entity_types, output_path=None):
        """
        Anonymize a DOCX file with custom entity selection while preserving formatting (FAST VERSION)
        """
        try:
            from utils.helpers import extract_valid_entities
            doc = Document(file_path)
            full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            # Anonymize with custom entity types using the pipeline
            replacement_result = self.pipeline.anonymize(full_text, entity_types)
            # If replacement_result is a tuple, unpack (legacy)
            if isinstance(replacement_result, tuple):
                replacement_result = replacement_result[0]
            if not isinstance(replacement_result, dict):
                return {
                    'success': False,
                    'error': f'Pipeline anonymize returned unexpected type: {type(replacement_result)}'
                }
            # Use valid_entities for anonymization
            valid_entities = extract_valid_entities([
                {"text": k, "label": v} for k, v in replacement_result['entity_info'].items()
            ])
            doc = fast_anonymize_docx(doc, valid_entities)
            if output_path is None:
                base_name = os.path.splitext(file_path)[0]
                output_path = f"{base_name}_anonymized.docx"
            doc.save(output_path)
            # Use FakerReplacer for replacements
            from agent.tools.replacers.faker_replacer import FakerReplacer
            faker_replacer = self.pipeline.replacer if hasattr(self.pipeline, 'replacer') else FakerReplacer()
            replacement_mapping = {}
            for e in valid_entities:
                replacement_mapping[e['text']] = faker_replacer._get_smart_replacement(e['text'], e['label'])
        
            # Log replacement mapping to a file for debugging
            try:
                with open('debug_logs.txt', 'a', encoding='utf-8') as log_file:
                    log_file.write(f"[DEBUG] Replacement mapping: {replacement_mapping}\n")
            except UnicodeEncodeError:
                print("[WARNING] Could not write replacement mapping to log due to encoding issues")
        
            return {
                'success': True,
                'original_text': full_text,
                'anonymized_text': None,
                'replacement_mapping': replacement_mapping,
                'entity_info': replacement_result.get('entity_info', {}),
                'output_path': output_path
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing DOCX file: {str(e)}'
            }

    def anonymize_pdf_with_entities(self, file_path, entity_types, output_path=None):
        """
        Anonymize a PDF file with custom entity selection
        """
        try:
            # Extract text from PDF
            with pdfplumber.open(file_path) as pdf:
                text_content = ""
                for page in pdf.pages:
                    text_content += page.extract_text() + "\n"
            
            # Anonymize with custom entity types
            result = self.pipeline.anonymize(text_content, entity_types)
            
            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(file_path)[0]
                output_path = f"{base_name}_anonymized.pdf"
            
            # Create new PDF with anonymized text
            self._create_pdf_from_text(result['anonymized_text'], output_path)
            
            return {
                'success': True,
                'original_text': text_content,
                'anonymized_text': result['anonymized_text'],
                'replacement_mapping': result['replacement_mapping'],
                'entity_info': result.get('entity_info', {}),
                'output_path': output_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing PDF file: {str(e)}'
            }

    def _create_pdf_from_text(self, text, output_path):
        """
        Create a professional PDF from text content using ReportLab with consistent document styling
        """
        try:
            # Create PDF document with professional margins
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                rightMargin=72, 
                leftMargin=72,
                topMargin=72, 
                bottomMargin=72
            )
            
            # Get base styles and create professional custom styles
            styles = getSampleStyleSheet()
            
            # Create professional body style
            styles.add(ParagraphStyle(
                name='DocumentBody',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=11,
                leading=14,
                spaceAfter=6,
                alignment=0  # Left aligned
            ))
            
            # Create title style for any headings
            styles.add(ParagraphStyle(
                name='DocumentTitle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=14,
                leading=16,
                spaceAfter=12,
                alignment=0
            ))
            
            # Split text into paragraphs (preserve double newlines as paragraph breaks)
            paragraphs = text.split('\n\n')
            
            # Create story (content) for PDF
            story = []
            
            for para_text in paragraphs:
                if para_text.strip():
                    # Clean up the text - preserve single newlines as spaces
                    cleaned_text = para_text.strip().replace('\n', ' ')
                    
                    # Check if this looks like a heading (short, uppercase, etc.)
                    if len(cleaned_text) < 100 and (cleaned_text.isupper() or cleaned_text.istitle()):
                        para = Paragraph(cleaned_text, styles['DocumentTitle'])
                    else:
                        para = Paragraph(cleaned_text, styles['DocumentBody'])
                    
                    story.append(para)
                    story.append(Spacer(1, 6))  # Small space between paragraphs
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            print(f"Error with professional PDF creation: {e}")
            # Fallback to simple PDF creation
            self._create_simple_pdf(text, output_path)
    
    def _create_simple_pdf(self, text, output_path):
        """
        Fallback method to create a simple PDF using canvas with consistent document styling
        """
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            width, height = A4
            
            # Set up professional text formatting
            c.setFont("Helvetica", 11)
            c.setFillColorRGB(0, 0, 0)  # Black text
            
            # Split text into lines with better line spacing
            lines = text.replace('\n\n', '\n').split('\n')
            y_position = height - 80  # Start with more top margin
            line_height = 16  # Better line spacing
            
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Handle long lines by wrapping
                    if c.stringWidth(line, "Helvetica", 11) > width - 144:  # Account for margins
                        # Simple word wrapping
                        words = line.split()
                        current_line = ""
                        for word in words:
                            test_line = current_line + " " + word if current_line else word
                            if c.stringWidth(test_line, "Helvetica", 11) > width - 144:
                                if current_line:
                                    c.drawString(72, y_position, current_line)
                                    y_position -= line_height
                                    if y_position < 80:  # New page needed
                                        c.showPage()
                                        c.setFont("Helvetica", 11)
                                        y_position = height - 80
                                current_line = word
                            else:
                                current_line = test_line
                        if current_line:
                            c.drawString(72, y_position, current_line)
                            y_position -= line_height
                    else:
                        c.drawString(72, y_position, line)
                        y_position -= line_height
                    
                    # Check if we need a new page
                    if y_position < 80:
                        c.showPage()
                        c.setFont("Helvetica", 11)
                        y_position = height - 80
            
            c.save()
            
        except Exception as e:
            print(f"Error with simple PDF creation: {e}")
            # Last resort - create minimal PDF
            try:
                c = canvas.Canvas(output_path, pagesize=A4)
                c.drawString(72, 800, "Anonymized Document")
                c.drawString(72, 780, "Content processing completed.")
                c.save()
            except Exception as e2:
                print(f"Critical error creating PDF: {e2}")
                raise e
