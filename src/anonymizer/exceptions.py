class AnonymizerError(Exception):
    """Base exception for anonymizer errors."""
    pass


class ScannedDocumentError(AnonymizerError):
    """Raised when a PDF page has no extractable text layer."""
    
    def __init__(self, page_number: int):
        self.page_number = page_number
        super().__init__(f"Page {page_number} has no text layer (scanned document?)")