import io
from typing import Tuple, Optional

def extract_text_from_file(file, filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract text from uploaded file.
    
    Returns:
        Tuple[text, error_message]: Text content if successful, error message if failed
    """
    try:
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.txt'):
            # Handle text files
            content = file.read().decode('utf-8')
            return content, None
            
        elif filename_lower.endswith('.pdf'):
            # Handle PDF files - try multiple libraries
            text_content = None
            pdfplumber_available = False
            pypdf2_available = False
            
            # Try pdfplumber first (often more reliable)
            try:
                import pdfplumber
                pdfplumber_available = True
                
                # Reset file pointer to beginning
                file.seek(0)
                
                with pdfplumber.open(io.BytesIO(file.read())) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                
                if text_content and text_content.strip():
                    return text_content.strip(), None
                    
            except ImportError:
                pass  # Try next method
            except Exception as e:
                pass  # Try next method
            
            # Try PyPDF2 as fallback
            try:
                import PyPDF2
                pypdf2_available = True
                
                # Reset file pointer to beginning
                file.seek(0)
                
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
                
                # Extract text from all pages
                text_content = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
                
                if text_content and text_content.strip():
                    return text_content.strip(), None
                    
            except ImportError:
                pass  # No PDF libraries available
            except Exception as e:
                pass
            
            # Check what happened
            if not pdfplumber_available and not pypdf2_available:
                return None, "PDF processing libraries not available. Please save your PDF as a .txt file and upload that instead."
            elif text_content is None or not text_content.strip():
                return None, "PDF appears to be empty, scanned, or contains only images. Please try converting to text format first."
            else:
                # Should not reach here, but just in case
                return text_content.strip() if text_content else "", None
                
        elif filename_lower.endswith('.docx'):
            # Handle Word documents
            try:
                from docx import Document
                
                # Reset file pointer to beginning
                file.seek(0)
                
                # Read DOCX file
                doc = Document(io.BytesIO(file.read()))
                
                # Extract text from all paragraphs
                text_content = ""
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
                
                if not text_content.strip():
                    return None, "Word document appears to be empty."
                
                return text_content.strip(), None
                
            except ImportError:
                return None, "Word document processing library not available. Please install python-docx."
            except Exception as e:
                return None, f"Error reading Word document: {str(e)}"
                
        else:
            # Unsupported file type
            supported_types = ['.txt', '.pdf', '.docx']
            return None, f"Unsupported file type. Supported formats: {', '.join(supported_types)}"
            
    except Exception as e:
        return None, f"Unexpected error processing file: {str(e)}"
