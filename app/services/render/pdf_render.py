"""PDF rendering for translated output."""
import logging
from pathlib import Path
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


def _register_fonts():
    """Register fonts that support Vietnamese characters."""
    try:
        # Try to register a Unicode-capable font
        # DejaVuSans is commonly available and supports Vietnamese
        import os
        
        # Common font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/seguiemj.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("VietnameseFont", font_path))
                logger.info(f"Registered font: {font_path}")
                return "VietnameseFont"
        
        logger.warning("No Vietnamese-capable font found, using default")
        return "Helvetica"
        
    except Exception as e:
        logger.warning(f"Font registration failed: {e}, using default")
        return "Helvetica"


def render_pdf(paragraphs: List[str], output_path: Path) -> Path:
    """Render translated paragraphs to a PDF file.
    
    Args:
        paragraphs: List of translated text paragraphs.
        output_path: Path where PDF should be saved.
        
    Returns:
        Path to the created PDF file.
    """
    logger.info(f"Rendering {len(paragraphs)} paragraphs to PDF: {output_path}")
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    # Register font and create styles
    font_name = _register_fonts()
    styles = getSampleStyleSheet()
    
    # Custom style for body text
    body_style = ParagraphStyle(
        'VietnameseBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=12,
    )
    
    # Build content
    content = []
    
    for para in paragraphs:
        if para.strip():
            # Escape XML special characters
            safe_text = (para
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
            )
            try:
                p = Paragraph(safe_text, body_style)
                content.append(p)
                content.append(Spacer(1, 6))
            except Exception as e:
                logger.warning(f"Failed to render paragraph: {e}")
                # Skip problematic paragraphs
                continue
    
    if not content:
        # Add a placeholder if no content
        content.append(Paragraph("(No translatable content found)", body_style))
    
    # Build PDF
    try:
        doc.build(content)
        logger.info(f"PDF created successfully: {output_path}")
    except Exception as e:
        logger.error(f"Failed to build PDF: {e}")
        raise
    
    return output_path
