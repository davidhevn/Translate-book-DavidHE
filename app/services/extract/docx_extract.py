"""DOCX text extraction."""
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def extract_docx(file_path: Path) -> List[str]:
    """Extract paragraphs from a DOCX file.
    
    Args:
        file_path: Path to DOCX file.
        
    Returns:
        List of paragraph texts.
    """
    try:
        from docx import Document
        
        doc = Document(file_path)
        paragraphs = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        
        logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Failed to extract DOCX: {e}")
        raise
