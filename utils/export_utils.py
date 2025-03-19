import os
import io
from typing import Optional, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def generate_pdf(transcription: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate a PDF file from a transcription.
    
    Args:
        transcription: Transcription dictionary from the database
        output_path: Path to save the PDF file (optional)
        
    Returns:
        Path to the generated PDF file
    """
    # If no output path is provided, create one in the current directory
    if output_path is None:
        filename = transcription['original_filename'].rsplit('.', 1)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{filename}_{timestamp}.pdf"
    
    # Create a PDF buffer
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Transcription - {transcription['original_filename']}")
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Custom style for transcription text
    transcription_style = ParagraphStyle(
        'TranscriptionStyle',
        parent=normal_style,
        spaceBefore=6,
        spaceAfter=6,
        leading=14
    )
    
    # Create document content
    content = []
    
    # Add title
    content.append(Paragraph(f"Transcription: {transcription['original_filename']}", title_style))
    content.append(Spacer(1, 12))
    
    # Add metadata table
    metadata = [
        ['File Name:', transcription['original_filename']],
        ['Duration:', f"{transcription['duration_seconds']:.2f} seconds"],
        ['File Type:', transcription['file_type']],
        ['Date:', transcription['created_at']]
    ]
    
    metadata_table = Table(metadata, colWidths=[100, 350])
    metadata_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(metadata_table)
    content.append(Spacer(1, 20))
    
    # Add processed transcription
    content.append(Paragraph("Processed Transcription:", heading_style))
    content.append(Spacer(1, 6))
    
    # Split the processed transcription into paragraphs and add each as a Paragraph
    for paragraph in transcription['processed_transcription'].split('\n\n'):
        if paragraph.strip():
            content.append(Paragraph(paragraph, transcription_style))
            content.append(Spacer(1, 6))
    
    # Build the PDF document
    doc.build(content)
    
    # Get the PDF content from the buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Write the PDF to a file
    with open(output_path, 'wb') as f:
        f.write(pdf_content)
    
    return output_path

def export_plaintext(transcription: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Export a transcription as plaintext.
    
    Args:
        transcription: Transcription dictionary from the database
        output_path: Path to save the text file (optional)
        
    Returns:
        Path to the generated text file
    """
    # If no output path is provided, create one in the current directory
    if output_path is None:
        filename = transcription['original_filename'].rsplit('.', 1)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{filename}_{timestamp}.txt"
    
    # Create the text content
    content = f"Transcription: {transcription['original_filename']}\n"
    content += f"Duration: {transcription['duration_seconds']:.2f} seconds\n"
    content += f"File Type: {transcription['file_type']}\n"
    content += f"Date: {transcription['created_at']}\n\n"
    content += f"Processed Transcription:\n\n"
    content += transcription['processed_transcription']
    
    # Write the text to a file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path
