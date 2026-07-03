#!/usr/bin/env python3
"""
Simple script to convert the markdown review to PDF using reportlab
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
import re

def create_pdf_from_markdown(md_file, pdf_file):
    """Convert markdown to PDF with basic formatting"""

    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1a1a1a',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor='#34495e',
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    h4_style = ParagraphStyle(
        'CustomH4',
        parent=styles['Heading4'],
        fontSize=11,
        textColor='#555555',
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#333333',
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    bold_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    # Parse markdown content
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            elements.append(Spacer(1, 0.1*inch))
            i += 1
            continue

        # Title (# )
        if line.startswith('# '):
            text = line[2:].strip()
            elements.append(Paragraph(text, title_style))
            elements.append(Spacer(1, 0.2*inch))

        # H2 (##)
        elif line.startswith('## '):
            text = line[3:].strip()
            elements.append(Paragraph(text, h2_style))

        # H3 (###)
        elif line.startswith('### '):
            text = line[4:].strip()
            elements.append(Paragraph(text, h3_style))

        # H4 (####)
        elif line.startswith('#### '):
            text = line[5:].strip()
            elements.append(Paragraph(text, h4_style))

        # Horizontal rule
        elif line.startswith('---'):
            elements.append(Spacer(1, 0.2*inch))
            elements.append(PageBreak())

        # Bold text or list items
        elif line.startswith('**') or line.startswith('- ') or line.startswith('1. '):
            # Clean up markdown formatting - properly handle bold
            text = line
            # Replace **text** with <b>text</b>
            import re
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = text.replace('★', '&#9733;')
            text = text.replace('✅', '&#10003;')

            # Handle bullet points
            if line.startswith('- '):
                text = '• ' + text[2:]

            elements.append(Paragraph(text, body_style))

        # Regular paragraph
        else:
            import re
            text = line
            # Replace **text** with <b>text</b>
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = text.replace('★', '&#9733;')
            text = text.replace('✅', '&#10003;')
            elements.append(Paragraph(text, body_style))

        i += 1

    # Build PDF
    doc.build(elements)
    print(f"PDF created successfully: {pdf_file}")

if __name__ == "__main__":
    create_pdf_from_markdown(
        "Professional_Review_Report.md",
        "Professional_Review_Report.pdf"
    )
