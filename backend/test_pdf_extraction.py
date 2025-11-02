#!/usr/bin/env python
"""Test PDF extraction directly with consolidated.pdf"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.balance_sheets.gemini_pdf_extractor import GeminiPDFExtractor
from apps.balance_sheets.pdf_processor import PDFProcessor
from django.core.files import File

def test_extraction(pdf_path):
    """Test extraction on the actual PDF file"""
    print("=" * 80)
    print("TESTING PDF EXTRACTION")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"\n❌ PDF file not found: {pdf_path}")
        return
    
    print(f"\n📄 Testing with: {pdf_path}")
    print(f"   File size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB\n")
    
    # Test Gemini extraction
    print("\n--- GEMINI 2.5 FLASH EXTRACTION ---")
    try:
        with open(pdf_path, 'rb') as f:
            gemini_extractor = GeminiPDFExtractor()
            result = gemini_extractor.extract_financial_data(f)
            
            print(f"\nExtraction Result:")
            print(f"  Overall Confidence: {result.get('confidence', {}).get('overall', 0):.2%}")
            
            data = result.get('data', {})
            print(f"\nExtracted Data:")
            for key, value in data.items():
                if value is not None:
                    print(f"  {key}: {value}")
            
            confidence_by_field = result.get('confidence', {}).get('by_field', {})
            if confidence_by_field:
                print(f"\nConfidence by Field:")
                for field, conf in confidence_by_field.items():
                    print(f"  {field}: {conf:.2%}")
            
            validation = result.get('validation', {})
            print(f"\nValidation:")
            print(f"  Balance Check: {validation.get('balance_check', False)}")
            if validation.get('warnings'):
                print(f"  Warnings: {validation.get('warnings')}")
            
            metadata = result.get('metadata', {})
            if metadata:
                print(f"\nMetadata:")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
                    
    except Exception as e:
        print(f"\n❌ Gemini extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test fallback extraction
    print("\n\n--- FALLBACK PDF PROCESSOR EXTRACTION ---")
    try:
        with open(pdf_path, 'rb') as f:
            processor = PDFProcessor()
            result = processor.extract_financial_data(f)
            
            print(f"\nExtracted Data (Fallback):")
            for key, value in result.items():
                if value is not None:
                    print(f"  {key}: {value}")
                    
    except Exception as e:
        print(f"\n❌ Fallback extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with consolidated.pdf
    pdf_path = "backend/apps/balance_sheets/consolidated.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "media/balance_sheets/consolidated.pdf"
    
    test_extraction(pdf_path)

