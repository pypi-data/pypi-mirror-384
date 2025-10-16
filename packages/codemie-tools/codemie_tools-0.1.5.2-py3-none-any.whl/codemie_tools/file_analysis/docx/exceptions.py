class DocxProcessingError(Exception):
    """Base exception for DOCX processing errors."""
    pass


class DocumentReadError(DocxProcessingError):
    """Error reading DOCX document."""
    pass


class DocumentWriteError(DocxProcessingError):
    """Error writing DOCX document."""
    pass


class CorruptedDocumentError(DocxProcessingError):
    """Error when document is corrupted."""
    pass


class UnsupportedFormatError(DocxProcessingError):
    """Error when document format is not supported."""
    pass


class AnalysisError(DocxProcessingError):
    """Error during document analysis."""
    pass


class InsufficientContentError(DocxProcessingError):
    """Error when document content is insufficient for analysis."""
    pass


class ExtractionError(DocxProcessingError):
    """Error extracting content from document."""
    pass


class OCRError(DocxProcessingError):
    """Error during OCR processing."""
    pass


class ImageExtractionError(DocxProcessingError):
    """Error extracting images from document."""
    pass


class TableExtractionError(DocxProcessingError):
    """Error extracting tables from document."""
    pass


class InvalidPageSelectionError(DocxProcessingError):
    """Error when page selection format is invalid."""
    pass