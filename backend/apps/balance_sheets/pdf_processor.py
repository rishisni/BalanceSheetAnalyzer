import pdfplumber
import google.generativeai as genai
from django.conf import settings
from io import BytesIO
import json


class PDFProcessor:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def extract_text_and_tables(self, pdf_file):
        """Extract text and tables from PDF using pdfplumber"""
        text_content = []
        tables_content = []
        
        with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text
                text = page.extract_text()
                if text:
                    text_content.append(f"Page {page_num}:\n{text}\n")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables, 1):
                        tables_content.append({
                            'page': page_num,
                            'table': table_num,
                            'data': table
                        })
        
        return '\n'.join(text_content), tables_content
    
    def extract_financial_data(self, pdf_file):
        """Extract financial data from balance sheet PDF"""
        text, tables = self.extract_text_and_tables(pdf_file)
        
        # Basic extraction - looking for common financial terms
        financial_data = {
            'total_assets': None,
            'current_assets': None,
            'non_current_assets': None,
            'total_liabilities': None,
            'current_liabilities': None,
            'non_current_liabilities': None,
            'total_equity': None,
            'revenue': None,
            'sales': None,
        }
        
        # Simple keyword-based extraction from text
        keywords_map = {
            'total_assets': ['total assets', 'total asset', 'total assets &'],
            'current_assets': ['current assets', 'current asset'],
            'non_current_assets': ['non-current assets', 'non-current asset', 'fixed assets'],
            'total_liabilities': ['total liabilities', 'total liability'],
            'current_liabilities': ['current liabilities', 'current liability'],
            'non_current_liabilities': ['non-current liabilities', 'non-current liability'],
            'total_equity': ['total equity', 'shareholders equity', 'share capital'],
            'revenue': ['total revenue', 'revenue'],
            'sales': ['total sales', 'sales'],
        }
        
        # Extract from text
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            for key, keywords in keywords_map.items():
                for keyword in keywords:
                    if keyword in line_lower:
                        # Try to extract number
                        value = self._extract_number_from_line(line)
                        if value and financial_data[key] is None:
                            financial_data[key] = value
                        break
        
        # If tables exist, try to extract from tables
        if tables and len(tables) > 0:
            # Process first table with financial data
            table_data = self._extract_from_table(tables[0]['data'])
            for key, value in table_data.items():
                if financial_data[key] is None and value is not None:
                    financial_data[key] = value
        
        return financial_data
    
    def _extract_number_from_line(self, line):
        """Extract number from a line of text"""
        import re
        # Remove commas and extract numbers
        numbers = re.findall(r'[\d,]+\.?\d*', line)
        if numbers:
            try:
                # Take the last number (usually the value)
                value_str = numbers[-1].replace(',', '')
                return float(value_str)
            except:
                return None
        return None
    
    def _extract_from_table(self, table_data):
        """Extract financial data from table"""
        financial_data = {}
        
        if not table_data:
            return financial_data
        
        # Look for patterns in the table
        for row in table_data:
            if row and len(row) >= 2:
                row_text = ' '.join([str(cell) for cell in row if cell]).lower()
                # Try to match financial terms
                if 'total assets' in row_text:
                    value = self._extract_number_from_cells(row[1:])
                    if value:
                        financial_data['total_assets'] = value
                elif 'current assets' in row_text:
                    value = self._extract_number_from_cells(row[1:])
                    if value:
                        financial_data['current_assets'] = value
                elif 'total liabilities' in row_text:
                    value = self._extract_number_from_cells(row[1:])
                    if value:
                        financial_data['total_liabilities'] = value
                elif 'total equity' in row_text or 'shareholders equity' in row_text:
                    value = self._extract_number_from_cells(row[1:])
                    if value:
                        financial_data['total_equity'] = value
        
        return financial_data
    
    def _extract_number_from_cells(self, cells):
        """Extract number from table cells"""
        for cell in cells:
            if cell:
                value = self._extract_number_from_line(str(cell))
                if value:
                    return value
        return None

