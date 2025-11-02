#!/usr/bin/env python
"""Debug extraction to see raw Gemini response"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import google.generativeai as genai
from django.conf import settings
from io import BytesIO
import json
import pdfplumber

def debug_extraction():
    """Debug the extraction process step by step"""
    pdf_path = "backend/apps/balance_sheets/consolidated.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = "media/balance_sheets/consolidated.pdf"
    
    print("=" * 80)
    print("DEBUGGING GEMINI EXTRACTION")
    print("=" * 80)
    
    if not settings.GEMINI_API_KEY:
        print("❌ Gemini API key not configured")
        return
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        extracted_text = ""
        for i, page in enumerate(pdf.pages[:10]):  # First 10 pages only
            text = page.extract_text()
            if text:
                extracted_text += f"\n--- Page {page.page_number} ---\n{text}\n"
    
    print(f"\nExtracted {len(extracted_text)} characters from first 10 pages")
    print(f"Preview: {extracted_text[:500]}...\n")
    
    # Create prompt
    prompt = f"""Extract balance sheet data from this PDF. Return ONLY valid JSON.

PDF Content:
{extracted_text[:10000]}

Extract:
- year (integer)
- quarter (string or null)
- currency_unit (string)
- total_assets (number)
- current_assets (number or null)
- total_liabilities (number)
- total_equity (number)
- revenue (number or null)
- sales (number or null)

Return JSON:
{{
    "year": 2024,
    "quarter": "Q4",
    "currency_unit": "INR Crores",
    "data": {{
        "total_assets": {{"value": 1234567, "confidence": 0.95}},
        "current_assets": {{"value": 500000, "confidence": 0.90}},
        "total_liabilities": {{"value": 800000, "confidence": 0.95}},
        "total_equity": {{"value": 434567, "confidence": 0.95}},
        "revenue": {{"value": 900000, "confidence": 0.88}},
        "sales": {{"value": 900000, "confidence": 0.88}}
    }},
    "validation": {{
        "balance_check_passed": true,
        "confidence_avg": 0.93
    }}
}}"""

    print("\n--- Sending to Gemini ---")
    print(f"Prompt length: {len(prompt)} chars\n")
    
    try:
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        print("--- Raw Response ---")
        print(f"Response type: {type(response)}")
        print(f"Has text attr: {hasattr(response, 'text')}")
        
        if hasattr(response, 'text'):
            response_text = response.text
            print(f"\nResponse text (first 500 chars):")
            print(response_text[:500])
            print(f"\nFull response text length: {len(response_text)}")
            
            # Try to parse
            try:
                # Remove markdown if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                result = json.loads(response_text)
                print("\n--- Parsed JSON ---")
                print(json.dumps(result, indent=2))
                
                # Check data structure
                data_section = result.get('data', result)
                print("\n--- Extracted Values ---")
                for key in ['total_assets', 'current_assets', 'total_liabilities', 'total_equity', 'revenue', 'sales']:
                    value = data_section.get(key)
                    if isinstance(value, dict):
                        print(f"{key}: {value.get('value')} (confidence: {value.get('confidence')})")
                    else:
                        print(f"{key}: {value}")
                        
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON parsing failed: {e}")
                print(f"Trying to find JSON in response...")
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        print("Found JSON!")
                        print(json.dumps(result, indent=2))
                    except:
                        print("Could not parse extracted JSON")
        else:
            print("Response does not have 'text' attribute")
            print(f"Response attributes: {dir(response)}")
            if hasattr(response, 'candidates'):
                print(f"Candidates: {response.candidates}")
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_extraction()

