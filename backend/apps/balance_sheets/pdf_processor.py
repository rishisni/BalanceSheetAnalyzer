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
        """Extract financial data from balance sheet, P&L, and cash flow PDF"""
        text, tables = self.extract_text_and_tables(pdf_file)
        
        # Initialize full set of financial fields
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
            'operating_cash_flow': None,
            'investing_cash_flow': None,
            'financing_cash_flow': None,
            'net_cash_flow': None,
            'current_ratio': None,
            'debt_to_equity': None,
            'roe': None,
        }
        
        # Expanded keyword map
        keywords_map = {
            # Assets & Liabilities
            'total_assets': ['total assets', 'total asset'],
            'current_assets': ['current assets'],
            'non_current_assets': ['non-current assets', 'fixed assets'],
            'total_liabilities': ['total liabilities'],
            'current_liabilities': ['current liabilities'],
            'non_current_liabilities': ['non-current liabilities'],
            'total_equity': ['total equity', 'shareholders equity', 'share capital'],
            # Revenue
            'revenue': ['total revenue', 'income', 'operating revenue'],
            'sales': ['sales', 'turnover'],
            # Cash flows
            'operating_cash_flow': ['net cash from operating activities', 'cash from operations', 'operating activities'],
            'investing_cash_flow': ['cash from investing activities', 'net cash used in investing'],
            'financing_cash_flow': ['cash from financing activities', 'net cash used in financing'],
            'net_cash_flow': ['net increase in cash', 'net decrease in cash', 'net cash flow'],
            # Ratios
            'current_ratio': ['current ratio'],
            'debt_to_equity': ['debt to equity', 'debt-equity ratio'],
            'roe': ['return on equity', 'roe']
        }
        
        # Keyword-based extraction from text
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            for key, keywords in keywords_map.items():
                for keyword in keywords:
                    if keyword in line_lower:
                        value = self._extract_number_from_line(line)
                        if value is not None and financial_data[key] is None:
                            financial_data[key] = value
                        break
        
        # Extract from tables (structured)
        if tables:
            for table in tables:
                table_data = self._extract_from_table(table['data'])
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
        """Extract structured financial data from a table"""
        financial_data = {}

        for row in table_data or []:
            if not row or len(row) < 2:
                continue
            
            row_text = ' '.join([str(cell).lower() for cell in row if cell])

            # Cash Flow
            if 'operating activities' in row_text:
                financial_data['operating_cash_flow'] = self._extract_number_from_cells(row[1:])
            elif 'investing activities' in row_text:
                financial_data['investing_cash_flow'] = self._extract_number_from_cells(row[1:])
            elif 'financing activities' in row_text:
                financial_data['financing_cash_flow'] = self._extract_number_from_cells(row[1:])
            elif 'net increase' in row_text or 'net decrease' in row_text:
                financial_data['net_cash_flow'] = self._extract_number_from_cells(row[1:])

            # Ratios
            elif 'current ratio' in row_text:
                financial_data['current_ratio'] = self._extract_number_from_cells(row[1:])
            elif 'debt to equity' in row_text or 'debt-equity' in row_text:
                financial_data['debt_to_equity'] = self._extract_number_from_cells(row[1:])
            elif 'return on equity' in row_text or 'roe' in row_text:
                financial_data['roe'] = self._extract_number_from_cells(row[1:])

            # Existing patterns (balance sheet)
            elif 'total assets' in row_text:
                financial_data['total_assets'] = self._extract_number_from_cells(row[1:])
            elif 'current assets' in row_text:
                financial_data['current_assets'] = self._extract_number_from_cells(row[1:])
            elif 'total liabilities' in row_text:
                financial_data['total_liabilities'] = self._extract_number_from_cells(row[1:])
            elif 'total equity' in row_text or 'shareholders equity' in row_text:
                financial_data['total_equity'] = self._extract_number_from_cells(row[1:])

        return financial_data


    def _extract_number_from_cells(self, cells):
        """Extract number from table cells"""
        for cell in cells:
            if cell:
                value = self._extract_number_from_line(str(cell))
                if value:
                    return value
        return None

