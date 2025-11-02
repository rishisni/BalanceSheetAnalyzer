#!/usr/bin/env python
"""Find which pages contain the balance sheet"""

import pdfplumber
from io import BytesIO

pdf_path = "backend/apps/balance_sheets/consolidated.pdf"
if not os.path.exists(pdf_path):
    pdf_path = "media/balance_sheets/consolidated.pdf"

print("=" * 80)
print("FINDING BALANCE SHEET PAGES")
print("=" * 80)

with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}\n")
    
    # Search for balance sheet keywords
    keywords = [
        'consolidated balance sheet',
        'total assets',
        'total liabilities',
        'shareholders equity',
        'financial position'
    ]
    
    balance_sheet_pages = []
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        text_lower = text.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        if matches >= 2:  # At least 2 keywords found
            balance_sheet_pages.append((i+1, matches, text[:200]))
    
    print("Pages likely containing balance sheet data:")
    print("-" * 80)
    for page_num, match_count, preview in balance_sheet_pages:
        print(f"\nPage {page_num} ({match_count} keywords matched):")
        print(f"  Preview: {preview}...")
    
    # Get a sample page with balance sheet
    if balance_sheet_pages:
        sample_page_num = balance_sheet_pages[0][0]
        print(f"\n\n=== FULL CONTENT OF PAGE {sample_page_num} ===")
        print(pdf.pages[sample_page_num-1].extract_text())

