"""
Document loaders for docpipe.

Focus: zero-dependency core with optional speed plugins.
"""

# Export main loader classes for direct use
from ._pdfium import PdfiumSerializer
from ._pymupdf import PyMuPDFSerializer
from ._docx import DocxSerializer

__all__ = ["PdfiumSerializer", "PyMuPDFSerializer", "DocxSerializer"]