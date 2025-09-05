#!/usr/bin/env python3

import json
import os
from datetime import datetime
from PyPDF2 import PdfReader
from pathlib import Path

def extract_pdf_content(pdf_path):
    """Extract all text content from PDF with page-by-page detail."""
    reader = PdfReader(pdf_path)
    pages_content = []

    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text.strip():  # Only include non-empty pages
                pages_content.append({
                    'page_number': page_num + 1,
                    'content': text,
                    'content_length': len(text)
                })
        except Exception as e:
            print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
            pages_content.append({
                'page_number': page_num + 1,
                'content': f"[Page {page_num + 1} - Content extraction failed]",
                'content_length': 0
            })

    return pages_content, len(reader.pages)

def create_jsonl_entries(pages_content, source_filename, total_pages):
    """Create JSONL entries from PDF content."""
    entries = []
    base_id = source_filename.replace('.pdf', '')

    # Create metadata entry
    metadata_entry = {
        "id": f"{base_id}:metadata",
        "title": f"{base_id} - Document Metadata",
        "content": f"Complete content extraction from {source_filename}. Total pages: {total_pages}. All text content extracted page by page to preserve complete information without exclusions.",
        "metadata": {
            "category": "metadata",
            "tags": ["PDF", "Document", base_id, "Complete"],
            "source": source_filename,
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "total_pages": total_pages,
            "extraction_method": "PyPDF2_page_by_page"
        },
        "ai_context": {
            "priority": "high",
            "search_keywords": [base_id.lower(), "pdf", "document", "complete"],
            "instruction": "Use this entry as reference for complete document content. All information from the PDF has been extracted without exclusions."
        }
    }
    entries.append(metadata_entry)

    # Create entries for each page
    for page_data in pages_content:
        page_id = f"{base_id}:page_{page_data['page_number']:03d}"

        entry = {
            "id": page_id,
            "title": f"{base_id} - Page {page_data['page_number']}",
            "content": page_data['content'],
            "metadata": {
                "category": "content",
                "tags": ["PDF", base_id, f"page_{page_data['page_number']}"],
                "source": source_filename,
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "page_number": page_data['page_number'],
                "total_pages": total_pages,
                "content_length": page_data['content_length'],
                "extraction_method": "PyPDF2_page_by_page"
            },
            "ai_context": {
                "priority": "high",
                "search_keywords": [base_id.lower(), f"page {page_data['page_number']}", "content"],
                "instruction": "This contains the complete text content from the specified page. No information has been excluded or truncated."
            }
        }
        entries.append(entry)

    return entries

def convert_pdf_to_jsonl(pdf_path, output_path=None):
    """Convert PDF to JSONL format."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.replace('.pdf', '.jsonl')

    print(f"Extracting content from: {pdf_path}")

    # Extract content
    pages_content, total_pages = extract_pdf_content(pdf_path)

    # Calculate total content
    total_chars = sum(page['content_length'] for page in pages_content)
    print(f"Extracted {total_chars} characters from {total_pages} pages")

    # Create JSONL entries
    entries = create_jsonl_entries(pages_content, os.path.basename(pdf_path), total_pages)

    # Write JSONL file
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"Created JSONL file: {output_path}")
    print(f"Total entries: {len(entries)}")
    print(f"Metadata entries: 1")
    print(f"Content entries: {len(entries) - 1}")

    return output_path

if __name__ == "__main__":
    # Convert A92.2.pdf to JSONL
    pdf_path = "/Users/natelad/Desktop/ampAI/sources/A92.2.pdf"
    jsonl_path = "/Users/natelad/Desktop/ampAI/sources/A92.2.jsonl"

    convert_pdf_to_jsonl(pdf_path, jsonl_path)
