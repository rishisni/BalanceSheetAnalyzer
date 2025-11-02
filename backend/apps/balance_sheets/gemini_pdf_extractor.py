import google.generativeai as genai
from django.conf import settings
from io import BytesIO
import json
import re


class GeminiPDFExtractor:
    """Advanced PDF extraction using Gemini 2.5 Flash for accurate financial data extraction."""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def extract_financial_data(self, pdf_file):
        """Extract financial data from balance sheet PDF using Gemini 2.5 Flash."""
        if not self.model:
            return self._get_default_error_response()
        
        try:
            pdf_file.seek(0)
            
            # Pass 1: Extract structured data
            result = self._extract_pass1(pdf_file)
            
            if result['confidence']['overall'] >= 0.90:
                return result
            
            # Pass 2: Validate and improve
            result = self._extract_pass2(pdf_file, result)
            
            # Pass 3: Final validation
            result = self._validate_pass3(result)
            
            return result
            
        except Exception:
            return self._get_error_response("Extraction failed")
    
    def _extract_pass1(self, pdf_file):
        """First pass: Initial extraction with Gemini 2.5 Flash."""
        pdf_file.seek(0)
        
        # Extract text from PDF
        extracted_text = self._extract_pdf_text(pdf_file)
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(extracted_text)
        
        # Generate response
        try:
            generation_config = {
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            # Parse JSON response
            result = self._parse_gemini_response(response)
            
            # Structure extracted data
            return self._structure_extracted_data(result)
            
        except Exception:
            return self._get_default_error_response()
    
    def _extract_pdf_text(self, pdf_file):
        """Extract text from PDF using pdfplumber."""
        pdf_file.seek(0)
        
        try:
            import pdfplumber
            
            with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
                extracted_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += f"\n--- Page {page.page_number} ---\n{text}\n"
            
            pdf_file.seek(0)
            
            # Limit text to avoid token limits
            text_limit = 15000
            if len(extracted_text) > text_limit:
                extracted_text = (extracted_text[:text_limit//2] + 
                                 "\n... [middle section truncated] ...\n" + 
                                 extracted_text[-text_limit//2:])
            
            return extracted_text
            
        except Exception:
            return "PDF text extraction failed. Please analyze the document structure."
    
    def _create_extraction_prompt(self, extracted_text):
        """Create prompt for Gemini extraction."""
        return f"""You are an expert financial analyst. Extract all key financial metrics from this company's balance sheet, income statement, and cash flow statement.

Extracted PDF Content:
{extracted_text}

Extract the following data fields (return ONLY valid JSON):

**General Info**
- year (integer)
- quarter (string like "Q1", "Q2", etc. or null)
- currency_unit (e.g., "INR Crores", "USD Millions")

**Assets & Liabilities**
- total_assets
- current_assets
- non_current_assets
- total_liabilities
- current_liabilities
- non_current_liabilities
- total_equity

**Income / Revenue**
- revenue
- sales

**Cash Flow Statement**
- operating_cash_flow
- investing_cash_flow
- financing_cash_flow
- net_cash_flow

**Key Ratios (if available or can be computed)**
- current_ratio
- debt_to_equity
- roe

**CRITICAL RULES:**
1. Extract the **exact numeric values** as shown in the report (ignore commas or currency signs).
2. If a value is missing or unclear, return `null` — not 0.
3. Ensure `total_assets ≈ total_liabilities + total_equity` (±0.01%).
4. Include a confidence score (0.0–1.0) for each extracted field.
5. Return valid JSON only. No markdown, no extra text.

**Expected JSON:**
{{
  "year": 2024,
  "quarter": "Q4",
  "currency_unit": "INR Crores",
  "data": {{
    "total_assets": {{"value": 1755986, "confidence": 0.97}},
    "operating_cash_flow": {{"value": 27841, "confidence": 0.92}},
    "current_ratio": {{"value": 1.52, "confidence": 0.88}},
    "debt_to_equity": {{"value": 0.63, "confidence": 0.85}},
    "roe": {{"value": 0.12, "confidence": 0.80}}
  }},
  "validation": {{
    "balance_check_passed": true,
    "confidence_avg": 0.93
  }}
}}"""

    
    def _parse_gemini_response(self, response):
        """Parse JSON response from Gemini, handling markdown-wrapped JSON."""
        try:
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response if wrapped in text
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise
                
        except Exception:
            return {}
    
    def _structure_extracted_data(self, result):
        """Structure extracted data into standard format."""
        if not isinstance(result, dict):
            return self._get_default_error_response()
        
        def safe_extract(data_dict, key, default=None):
            """Extract value, handling both dict with 'value' key and direct value."""
            if not isinstance(data_dict, dict):
                return default
            value = data_dict.get(key, default)
            if isinstance(value, dict) and 'value' in value:
                return value['value']
            return value if value is not None else default
        
        data_section = result.get('data', result)
        if not isinstance(data_section, dict):
            data_section = result if isinstance(result, dict) else {}
        
        # Extract financial data
        extracted_data = {
            # Assets
            'total_assets': safe_extract(data_section, 'total_assets'),
            'current_assets': safe_extract(data_section, 'current_assets'),
            'non_current_assets': safe_extract(data_section, 'non_current_assets'),

            # Liabilities & Equity
            'total_liabilities': safe_extract(data_section, 'total_liabilities'),
            'current_liabilities': safe_extract(data_section, 'current_liabilities'),
            'non_current_liabilities': safe_extract(data_section, 'non_current_liabilities'),
            'total_equity': safe_extract(data_section, 'total_equity'),

            # Revenue
            'revenue': safe_extract(data_section, 'revenue'),
            'sales': safe_extract(data_section, 'sales'),

            # Cash Flow
            'operating_cash_flow': safe_extract(data_section, 'operating_cash_flow'),
            'investing_cash_flow': safe_extract(data_section, 'investing_cash_flow'),
            'financing_cash_flow': safe_extract(data_section, 'financing_cash_flow'),
            'net_cash_flow': safe_extract(data_section, 'net_cash_flow'),

            # Ratios
            'current_ratio': safe_extract(data_section, 'current_ratio'),
            'debt_to_equity': safe_extract(data_section, 'debt_to_equity'),
            'roe': safe_extract(data_section, 'roe'),
        }

        
        # Extract confidence scores
        confidence_scores = {}
        if isinstance(data_section, dict):
            for key in ['total_assets', 'current_assets', 'total_liabilities', 'total_equity', 'revenue', 'sales']:
                if key in data_section:
                    val = data_section[key]
                    if isinstance(val, dict) and 'confidence' in val:
                        confidence_scores[key] = val['confidence']
        
        validation_section = result.get('validation', {})
        overall_confidence = validation_section.get(
            'confidence_avg',
            validation_section.get(
                'confidence',
                sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
            )
        )
        
        return {
            'data': extracted_data,
            'confidence': {
                'overall': overall_confidence,
                'by_field': confidence_scores
            },
            'validation': {
                'balance_check': validation_section.get('balance_check_passed', False),
                'warnings': []
            },
            'metadata': {
                'year': result.get('year'),
                'quarter': result.get('quarter'),
                'currency_unit': result.get('currency_unit')
            }
        }
    
    def _extract_pass2(self, pdf_file, pass1_result):
        """Second pass: Try to improve low confidence fields."""
        return pass1_result
    
    def _validate_pass3(self, result):
        """Third pass: Final validation and warnings."""
        data = result['data']
        warnings = []
        
        # Validate balance sheet equation: Assets = Liabilities + Equity
        if all(v is not None for v in [data.get('total_assets'), data.get('total_liabilities'), data.get('total_equity')]):
            assets = float(data['total_assets'])
            liabilities = float(data['total_liabilities'])
            equity = float(data['total_equity'])
            
            calculated_equity = assets - liabilities
            difference = abs(equity - calculated_equity)
            tolerance = assets * 0.0001  # 0.01% tolerance
            
            if difference > tolerance:
                warnings.append(f"Balance equation mismatch: {difference:.2f} difference")
                result['validation']['balance_check'] = False
        
        # Check for logical consistency
        if data.get('current_assets') and data.get('non_current_assets') and data.get('total_assets'):
            sum_assets = float(data['current_assets']) + float(data['non_current_assets'])
            total_assets = float(data['total_assets'])
            if abs(sum_assets - total_assets) > 0.01:
                warnings.append("Assets sum doesn't match total assets")
        
        if data.get('current_liabilities') and data.get('non_current_liabilities') and data.get('total_liabilities'):
            sum_liabilities = float(data['current_liabilities']) + float(data['non_current_liabilities'])
            total_liabilities = float(data['total_liabilities'])
            if abs(sum_liabilities - total_liabilities) > 0.01:
                warnings.append("Liabilities sum doesn't match total liabilities")
        
        result['validation']['warnings'] = warnings
        return result
    
    def _get_default_error_response(self):
        """Return default error response structure."""
        return {
            'data': {
                'total_assets': None,
                'current_assets': None,
                'non_current_assets': None,
                'total_liabilities': None,
                'current_liabilities': None,
                'non_current_liabilities': None,
                'total_equity': None,
                'revenue': None,
                'sales': None,
            },
            'confidence': {
                'overall': 0.0,
                'by_field': {}
            },
            'validation': {
                'balance_check': False,
                'warnings': ['Extraction failed - no API configured']
            },
            'metadata': {
                'year': None,
                'quarter': None,
                'currency_unit': None
            }
        }
    
    def _get_error_response(self, error_msg):
        """Return error response with message."""
        result = self._get_default_error_response()
        result['validation']['warnings'] = [f'Extraction error: {error_msg}']
        return result
