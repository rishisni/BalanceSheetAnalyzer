#!/usr/bin/env python
"""Test script to diagnose data extraction issues"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.balance_sheets.models import BalanceSheet, FinancialData, PDFChunk
from apps.companies.models import Company
import json

def check_existing_data():
    """Check what's currently in the database"""
    print("=" * 80)
    print("DATABASE DIAGNOSTICS")
    print("=" * 80)
    
    # Companies
    print("\n--- COMPANIES ---")
    companies = Company.objects.all()
    for c in companies:
        print(f"  {c.id}: {c.name}")
    
    # Balance Sheets
    print("\n--- BALANCE SHEETS ---")
    balance_sheets = BalanceSheet.objects.all()
    for bs in balance_sheets:
        print(f"\n  Balance Sheet ID: {bs.id}")
        print(f"    Company: {bs.company.name}")
        print(f"    Year: {bs.year}, Quarter: {bs.quarter or 'N/A'}")
        print(f"    Status: {bs.extraction_status}")
        print(f"    PDF: {bs.pdf_file.name if bs.pdf_file else 'None'}")
        print(f"    Uploaded: {bs.uploaded_at}")
        
        # Financial Data
        fd = bs.financial_data.first()
        if fd:
            print(f"    Financial Data:")
            print(f"      Total Assets: {fd.total_assets}")
            print(f"      Current Assets: {fd.current_assets}")
            print(f"      Total Liabilities: {fd.total_liabilities}")
            print(f"      Total Equity: {fd.total_equity}")
            print(f"      Revenue: {fd.revenue}")
            print(f"      Sales: {fd.sales}")
            if fd.additional_data:
                print(f"      Additional Data Keys: {list(fd.additional_data.keys())}")
                if 'confidence' in fd.additional_data:
                    print(f"      Confidence: {fd.additional_data.get('confidence', {}).get('overall', 'N/A')}")
        
        # Chunks
        chunk_count = PDFChunk.objects.filter(balance_sheet=bs).count()
        print(f"    PDF Chunks: {chunk_count}")
        if chunk_count > 0:
            chunks = PDFChunk.objects.filter(balance_sheet=bs)[:3]
            print(f"    Sample Chunks:")
            for c in chunks:
                print(f"      - {c.section_type} (Page {c.page_num}): {c.source_title[:50]}...")
                print(f"        Content length: {len(c.content)} chars")
                print(f"        Confidence: {c.confidence}")

def check_chunk_content(balance_sheet_id):
    """Check chunk content for a specific balance sheet"""
    print("\n" + "=" * 80)
    print(f"CHUNK CONTENT ANALYSIS for Balance Sheet {balance_sheet_id}")
    print("=" * 80)
    
    bs = BalanceSheet.objects.get(id=balance_sheet_id)
    chunks = PDFChunk.objects.filter(balance_sheet=bs).order_by('page_num')
    
    print(f"\nTotal chunks: {chunks.count()}")
    
    # Group by section type
    from collections import defaultdict
    by_section = defaultdict(list)
    for chunk in chunks:
        by_section[chunk.section_type].append(chunk)
    
    print("\nChunks by section:")
    for section_type, section_chunks in by_section.items():
        print(f"\n  {section_type}: {len(section_chunks)} chunks")
        for c in section_chunks[:2]:  # Show first 2
            print(f"    Page {c.page_num}: {c.source_title[:60]}")
            print(f"      Content preview: {c.content[:150]}...")

def check_financial_data_accuracy(balance_sheet_id):
    """Check if financial data makes sense"""
    print("\n" + "=" * 80)
    print(f"FINANCIAL DATA ACCURACY CHECK for Balance Sheet {balance_sheet_id}")
    print("=" * 80)
    
    bs = BalanceSheet.objects.get(id=balance_sheet_id)
    fd = bs.financial_data.first()
    
    if not fd:
        print("  No financial data found!")
        return
    
    print("\nExtracted Values:")
    print(f"  Total Assets: {fd.total_assets}")
    print(f"  Current Assets: {fd.current_assets}")
    print(f"  Non-Current Assets: {fd.non_current_assets}")
    print(f"  Total Liabilities: {fd.total_liabilities}")
    print(f"  Current Liabilities: {fd.current_liabilities}")
    print(f"  Non-Current Liabilities: {fd.non_current_liabilities}")
    print(f"  Total Equity: {fd.total_equity}")
    print(f"  Revenue: {fd.revenue}")
    print(f"  Sales: {fd.sales}")
    
    # Validation checks
    print("\nValidation Checks:")
    
    # Check balance sheet equation
    if fd.total_assets and fd.total_liabilities and fd.total_equity:
        assets = float(fd.total_assets)
        liabilities = float(fd.total_liabilities)
        equity = float(fd.total_equity)
        calculated_equity = assets - liabilities
        difference = abs(calculated_equity - equity)
        tolerance = assets * 0.001  # 0.1% tolerance
        
        print(f"  Balance Sheet Equation:")
        print(f"    Assets ({assets}) = Liabilities ({liabilities}) + Equity ({equity})")
        print(f"    Calculated Equity: {calculated_equity}")
        print(f"    Difference: {difference}")
        if difference < tolerance:
            print(f"    ✓ PASSED (within {tolerance:.2f} tolerance)")
        else:
            print(f"    ✗ FAILED (difference too large)")
    
    # Check component sums
    if fd.current_assets and fd.non_current_assets and fd.total_assets:
        ca = float(fd.current_assets)
        nca = float(fd.non_current_assets)
        ta = float(fd.total_assets)
        sum_assets = ca + nca
        diff = abs(ta - sum_assets)
        print(f"\n  Assets Components:")
        print(f"    Current ({ca}) + Non-Current ({nca}) = {sum_assets}")
        print(f"    Total Assets: {ta}, Difference: {diff}")
        if diff < ta * 0.01:
            print(f"    ✓ Components match")
        else:
            print(f"    ⚠ Warning: Components don't match total")

if __name__ == "__main__":
    print("\n🔍 DATA EXTRACTION DIAGNOSTIC TOOL\n")
    
    # Check existing data
    check_existing_data()
    
    # Check specific balance sheet if exists
    balance_sheets = BalanceSheet.objects.all()
    if balance_sheets.exists():
        bs_id = balance_sheets.first().id
        check_chunk_content(bs_id)
        check_financial_data_accuracy(bs_id)
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

