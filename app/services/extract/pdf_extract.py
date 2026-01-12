"""PDF text extraction."""
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def extract_pdf(file_path: Path) -> List[str]:
    """Extract text from a PDF file.
    
    Args:
        file_path: Path to PDF file.
        
    Returns:
        List of text paragraphs/blocks.
    """
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(file_path)
        paragraphs = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                # Split by double newlines to get paragraphs
                page_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                paragraphs.extend(page_paragraphs)
        
        logger.info(f"Extracted {len(paragraphs)} paragraphs from PDF ({len(reader.pages)} pages)")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Failed to extract PDF: {e}")
        raise
