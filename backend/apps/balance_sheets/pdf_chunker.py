"""PDF Chunking system matching the working hello.py approach."""
from django.conf import settings
from io import BytesIO
import json
import re
import os

# Use PyMuPDF (fitz) for better table extraction
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Use newer google-genai library if available, fallback to old one
try:
    from google import genai as google_genai
    from google.genai.errors import APIError
    USE_NEW_GENAI = True
except ImportError:
    try:
        import google.generativeai as google_genai
        USE_NEW_GENAI = False
    except ImportError:
        google_genai = None
        USE_NEW_GENAI = None


class PDFChunker:
    """Intelligent PDF chunking system matching hello.py approach."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY if hasattr(settings, 'GEMINI_API_KEY') else None
        
        if self.api_key and USE_NEW_GENAI is True:
            try:
                self.client = google_genai.Client(api_key=self.api_key)
                self.use_new_api = True
            except Exception:
                self.client = None
                self.use_new_api = False
        elif self.api_key and USE_NEW_GENAI is False:
            if google_genai:
                google_genai.configure(api_key=self.api_key)
            self.client = None
            self.use_new_api = False
        else:
            self.client = None
            self.use_new_api = False
    
    def extract_tables_and_text(self, pdf_file):
        """Extracts content (tables as Markdown, and text) with page numbers using PyMuPDF."""
        pdf_file.seek(0)
        content_list = []
        
        # Use PyMuPDF if available, otherwise fallback to pdfplumber
        if fitz:
            try:
                pdf_bytes = pdf_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                
                for page_num, page in enumerate(doc, 1):
                    text = page.get_text()
                    table_match = re.search(r"The following table:\n", text, re.IGNORECASE)
                    
                    if table_match:
                        narrative_content = text[:table_match.start()]
                        if narrative_content.strip():
                            content_list.append((narrative_content, page_num, 'Narrative_Text'))
                        
                        table_content = text[table_match.start():]
                        content_list.append((table_content, page_num, 'Raw_Table'))
                    else:
                        if text.strip():
                            content_list.append((text, page_num, 'Narrative_Text'))
                
                doc.close()
                pdf_file.seek(0)
                return content_list
                
            except Exception:
                pass
        
        # Fallback to pdfplumber
        try:
            import pdfplumber
            pdf_file.seek(0)
            with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        content_list.append((text, page_num, 'Narrative_Text'))
            pdf_file.seek(0)
            return content_list
        except Exception:
            return []
    
    def create_intelligent_chunks(self, content_blocks, company_id, balance_sheet_id):
        """Applies structure-aware chunking and injects metadata."""
        final_chunks = []
        
        narrative_splitter = re.compile(
            r'\n(Note|Notes|Contingent Liabilities and Commitments|Material Accounting Policies|Financial Instruments)\s*[\d\.]*\s*.*',
            re.IGNORECASE
        )
        
        fs_patterns = [
            (r'.*Consolidated Balance Sheet.*', 'BALANCE_SHEET'),
            (r'.*Consolidated Statement of Profit and Loss.*', 'INCOME_STATEMENT'),
            (r'.*Statement of Profit and Loss.*', 'INCOME_STATEMENT'),
            (r'.*Cash Flow.*', 'CASH_FLOW'),
            (r'.*Statement of Cash Flows.*', 'CASH_FLOW'),
        ]
        
        for content, page_num, block_type in content_blocks:
            
            if block_type == 'Raw_Table':
                title = None
                section_type = 'OTHER'
                
                for pattern, sec_type in fs_patterns:
                    title_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                    if title_match:
                        title = title_match.group(0).strip()
                        section_type = sec_type
                        break
                
                if not title:
                    title = f"Financial Statement Table - Page {page_num}"
                
                final_chunks.append({
                    'balance_sheet_id': balance_sheet_id,
                    'company_id': company_id,
                    'content': content,
                    'section_type': section_type,
                    'page_num': page_num,
                    'chunk_type': 'Table_FS',
                    'source_title': title[:200],
                    'start_page': page_num,
                    'end_page': page_num,
                })
            
            elif block_type == 'Narrative_Text':
                narrative_sections = narrative_splitter.split(content)
                
                if len(narrative_sections) > 1:
                    if narrative_sections[0].strip():
                        final_chunks.append({
                            'balance_sheet_id': balance_sheet_id,
                            'company_id': company_id,
                            'content': narrative_sections[0].strip(),
                            'section_type': 'NOTES',
                            'page_num': page_num,
                            'chunk_type': 'Narrative_Intro',
                            'source_title': "General Introduction/Auditor's Report",
                            'start_page': page_num,
                            'end_page': page_num,
                        })
                    
                    for i in range(1, len(narrative_sections), 2):
                        note_header = narrative_sections[i].strip() if i < len(narrative_sections) else "Misc Note"
                        note_content = narrative_sections[i+1].strip() if i + 1 < len(narrative_sections) else ""
                        
                        if note_content:
                            final_chunks.append({
                                'balance_sheet_id': balance_sheet_id,
                                'company_id': company_id,
                                'content': note_content,
                                'section_type': 'NOTES',
                                'page_num': page_num,
                                'chunk_type': 'Narrative_Note',
                                'source_title': note_header.split('\n')[0][:200],
                                'start_page': page_num,
                                'end_page': page_num,
                            })
                
                elif content.strip():
                    final_chunks.append({
                        'balance_sheet_id': balance_sheet_id,
                        'company_id': company_id,
                        'content': content.strip(),
                        'section_type': 'OTHER',
                        'page_num': page_num,
                        'chunk_type': 'Narrative_General',
                        'source_title': f"Page {page_num} General Text",
                        'start_page': page_num,
                        'end_page': page_num,
                    })
        
        return final_chunks
    
    def process_pdf(self, pdf_file, balance_sheet):
        """Main processing function: Extract → Chunk."""
        content_blocks = self.extract_tables_and_text(pdf_file)
        
        if not content_blocks:
            return []
        
        company_id = str(balance_sheet.company.id)
        balance_sheet_id = balance_sheet.id
        chunks = self.create_intelligent_chunks(content_blocks, company_id, balance_sheet_id)
        
        return chunks
    
    def extract_chunk(self, pdf_file, section_info):
        """Placeholder for chunk content extraction"""
        return {
            'content': 'Content extracted (Placeholder)',
            'summary': 'Summary (Placeholder)',
            'confidence': 0.85
        }

    def extract_structured_data_from_chunk(self, chunk_content, section_type):
        """Placeholder for structured data extraction"""
        return {}
