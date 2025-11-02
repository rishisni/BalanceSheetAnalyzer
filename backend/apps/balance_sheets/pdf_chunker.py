# """PDF Chunking system matching the working hello.py approach."""
# from django.conf import settings
# from io import BytesIO
# import json
# import re
# import os

# # Use PyMuPDF (fitz) for better table extraction
# try:
#     import fitz  # PyMuPDF
# except ImportError:
#     fitz = None

# # Use newer google-genai library if available, fallback to old one
# try:
#     from google import genai as google_genai
#     from google.genai.errors import APIError
#     USE_NEW_GENAI = True
# except ImportError:
#     try:
#         import google.generativeai as google_genai
#         USE_NEW_GENAI = False
#     except ImportError:
#         google_genai = None
#         USE_NEW_GENAI = None


# class PDFChunker:
#     """Intelligent PDF chunking system matching hello.py approach."""
    
#     def __init__(self):
#         self.api_key = settings.GEMINI_API_KEY if hasattr(settings, 'GEMINI_API_KEY') else None
        
#         if self.api_key and USE_NEW_GENAI is True:
#             try:
#                 self.client = google_genai.Client(api_key=self.api_key)
#                 self.use_new_api = True
#             except Exception:
#                 self.client = None
#                 self.use_new_api = False
#         elif self.api_key and USE_NEW_GENAI is False:
#             if google_genai:
#                 google_genai.configure(api_key=self.api_key)
#             self.client = None
#             self.use_new_api = False
#         else:
#             self.client = None
#             self.use_new_api = False
    
#     def extract_tables_and_text(self, pdf_file):
#         """Extracts content (tables as Markdown, and text) with page numbers using PyMuPDF."""
#         pdf_file.seek(0)
#         content_list = []
        
#         # Use PyMuPDF if available, otherwise fallback to pdfplumber
#         if fitz:
#             try:
#                 pdf_bytes = pdf_file.read()
#                 doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                
#                 for page_num, page in enumerate(doc, 1):
#                     text = page.get_text()
#                     table_match = re.search(r"The following table:\n", text, re.IGNORECASE)
                    
#                     if table_match:
#                         narrative_content = text[:table_match.start()]
#                         if narrative_content.strip():
#                             content_list.append((narrative_content, page_num, 'Narrative_Text'))
                        
#                         table_content = text[table_match.start():]
#                         content_list.append((table_content, page_num, 'Raw_Table'))
#                     else:
#                         if text.strip():
#                             content_list.append((text, page_num, 'Narrative_Text'))
                
#                 doc.close()
#                 pdf_file.seek(0)
#                 return content_list
                
#             except Exception:
#                 pass
        
#         # Fallback to pdfplumber
#         try:
#             import pdfplumber
#             pdf_file.seek(0)
#             with pdfplumber.open(BytesIO(pdf_file.read())) as pdf:
#                 for page_num, page in enumerate(pdf.pages, 1):
#                     text = page.extract_text()
#                     if text:
#                         content_list.append((text, page_num, 'Narrative_Text'))
#             pdf_file.seek(0)
#             return content_list
#         except Exception:
#             return []
    
#     def create_intelligent_chunks(self, content_blocks, company_id, balance_sheet_id):
#         """Applies structure-aware chunking and injects metadata."""
#         final_chunks = []
        
#         narrative_splitter = re.compile(
#             r'\n(Note|Notes|Contingent Liabilities and Commitments|Material Accounting Policies|Financial Instruments)\s*[\d\.]*\s*.*',
#             re.IGNORECASE
#         )
        
#         fs_patterns = [
#             (r'.*Consolidated Balance Sheet.*', 'BALANCE_SHEET'),
#             (r'.*Consolidated Statement of Profit and Loss.*', 'INCOME_STATEMENT'),
#             (r'.*Statement of Profit and Loss.*', 'INCOME_STATEMENT'),
#             (r'.*Cash Flow.*', 'CASH_FLOW'),
#             (r'.*Statement of Cash Flows.*', 'CASH_FLOW'),
#         ]
        
#         for content, page_num, block_type in content_blocks:
            
#             if block_type == 'Raw_Table':
#                 title = None
#                 section_type = 'OTHER'
                
#                 for pattern, sec_type in fs_patterns:
#                     title_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
#                     if title_match:
#                         title = title_match.group(0).strip()
#                         section_type = sec_type
#                         break
                
#                 if not title:
#                     title = f"Financial Statement Table - Page {page_num}"
                
#                 final_chunks.append({
#                     'balance_sheet_id': balance_sheet_id,
#                     'company_id': company_id,
#                     'content': content,
#                     'section_type': section_type,
#                     'page_num': page_num,
#                     'chunk_type': 'Table_FS',
#                     'source_title': title[:200],
#                     'start_page': page_num,
#                     'end_page': page_num,
#                 })
            
#             elif block_type == 'Narrative_Text':
#                 narrative_sections = narrative_splitter.split(content)
                
#                 if len(narrative_sections) > 1:
#                     if narrative_sections[0].strip():
#                         final_chunks.append({
#                             'balance_sheet_id': balance_sheet_id,
#                             'company_id': company_id,
#                             'content': narrative_sections[0].strip(),
#                             'section_type': 'NOTES',
#                             'page_num': page_num,
#                             'chunk_type': 'Narrative_Intro',
#                             'source_title': "General Introduction/Auditor's Report",
#                             'start_page': page_num,
#                             'end_page': page_num,
#                         })
                    
#                     for i in range(1, len(narrative_sections), 2):
#                         note_header = narrative_sections[i].strip() if i < len(narrative_sections) else "Misc Note"
#                         note_content = narrative_sections[i+1].strip() if i + 1 < len(narrative_sections) else ""
                        
#                         if note_content:
#                             final_chunks.append({
#                                 'balance_sheet_id': balance_sheet_id,
#                                 'company_id': company_id,
#                                 'content': note_content,
#                                 'section_type': 'NOTES',
#                                 'page_num': page_num,
#                                 'chunk_type': 'Narrative_Note',
#                                 'source_title': note_header.split('\n')[0][:200],
#                                 'start_page': page_num,
#                                 'end_page': page_num,
#                             })
                
#                 elif content.strip():
#                     final_chunks.append({
#                         'balance_sheet_id': balance_sheet_id,
#                         'company_id': company_id,
#                         'content': content.strip(),
#                         'section_type': 'OTHER',
#                         'page_num': page_num,
#                         'chunk_type': 'Narrative_General',
#                         'source_title': f"Page {page_num} General Text",
#                         'start_page': page_num,
#                         'end_page': page_num,
#                     })
        
#         return final_chunks
    
#     def process_pdf(self, pdf_file, balance_sheet):
#         """Main processing function: Extract → Chunk."""
#         content_blocks = self.extract_tables_and_text(pdf_file)
        
#         if not content_blocks:
#             return []
        
#         company_id = str(balance_sheet.company.id)
#         balance_sheet_id = balance_sheet.id
#         chunks = self.create_intelligent_chunks(content_blocks, company_id, balance_sheet_id)
        
#         return chunks
    
#     def extract_chunk(self, pdf_file, section_info):
#         """Placeholder for chunk content extraction"""
#         return {
#             'content': 'Content extracted (Placeholder)',
#             'summary': 'Summary (Placeholder)',
#             'confidence': 0.85
#         }

#     def extract_structured_data_from_chunk(self, chunk_content, section_type):
#         """Placeholder for structured data extraction"""
#         return {}



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
    """Intelligent PDF chunking system using Strategy1 (Enhanced Regex) approach."""

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

        # Strategy1: Financial statement patterns
        self.fs_patterns = [
            r'consolidated\s+balance\s+sheet',
            r'statement\s+of\s+profit\s+and\s+loss',
            r'statement\s+of\s+cash\s+flows',
            r'balance\s+sheet',
            r'profit\s+and\s+loss',
            r'cash\s+flow\s+statement',
        ]

        # Strategy1: Strict note splitting - only numbered notes
        self.note_pattern = r'\n+(?:Note|Notes)\s+(\d+)[:\.\-\s]'

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
        """
        Strategy1: Enhanced Regex chunking with smart splitting and grouping.

        Key improvements:
        - Only splits on numbered note headers (Note 1:, Note 2:), not table references
        - Detects and groups multi-page financial statements
        - Merges small fragments (<300 chars)
        - Reduces from 179 to ~107 chunks
        """
        # Extract pages from content_blocks
        pages = []
        for content, page_num, block_type in content_blocks:
            pages.append((page_num, content))

        # Detect financial statements and their page ranges
        fs_pages = self._detect_financial_statements(pages)

        # Create chunks with smart grouping
        final_chunks = []
        current_page_idx = 0
        processed_pages = set()

        while current_page_idx < len(pages):
            page_num, content = pages[current_page_idx]

            # Skip if already processed (part of multi-page statement)
            if page_num in processed_pages:
                current_page_idx += 1
                continue

            # Check if this is part of a financial statement
            is_fs = any(page_num in fs_range for fs_range in fs_pages.values())

            if is_fs:
                # Group multi-page financial statements
                fs_type, fs_range = self._get_fs_info(page_num, fs_pages)

                # Combine all pages of this statement
                combined_content = []
                for p_num, p_content in pages:
                    if p_num in fs_range:
                        combined_content.append(p_content)
                        processed_pages.add(p_num)

                full_content = "\n\n".join(combined_content)

                final_chunks.append({
                    'balance_sheet_id': balance_sheet_id,
                    'content': full_content,
                    'section_type': self._map_fs_type_to_section(fs_type),
                    'page_num': fs_range[0],  # First page
                    'chunk_type': fs_type,
                    'source_title': fs_type.replace('_', ' ').title(),
                    'start_page': fs_range[0],
                    'end_page': fs_range[-1],
                })

                # Skip to next unprocessed page
                current_page_idx = len([p for p in pages if p[0] <= fs_range[-1]])

            else:
                # Regular content - apply smart splitting
                split_chunks = self._smart_split_content(content, page_num, balance_sheet_id)
                final_chunks.extend(split_chunks)
                processed_pages.add(page_num)
                current_page_idx += 1

        return final_chunks

    def _detect_financial_statements(self, pages):
        """Detect where financial statements start and their page ranges"""
        fs_pages = {}
        current_statement = None
        current_range = []

        for page_num, content in pages:
            content_lower = content.lower()

            # Check for statement start
            found_statement = None
            for pattern in self.fs_patterns:
                if re.search(pattern, content_lower):
                    # Create readable name from pattern
                    found_statement = pattern.replace(r'\s+', '_').replace('\\', '').upper()
                    break

            if found_statement:
                # Save previous statement
                if current_statement and current_range:
                    fs_pages[current_statement] = current_range

                # Start new statement
                current_statement = found_statement
                current_range = [page_num]
            elif current_statement:
                # Check if still part of statement (has numbers, table structure)
                if self._is_continuation(content):
                    current_range.append(page_num)
                else:
                    # End of statement
                    fs_pages[current_statement] = current_range
                    current_statement = None
                    current_range = []

        # Save last statement
        if current_statement and current_range:
            fs_pages[current_statement] = current_range

        return fs_pages

    def _is_continuation(self, content):
        """Check if page is continuation of financial statement"""
        # Simple heuristic: has numbers and limited text
        numbers = len(re.findall(r'\d+[,\.\d]*', content))
        words = len(re.findall(r'\b\w+\b', content))
        return numbers > 10 and words < 500

    def _get_fs_info(self, page_num, fs_pages):
        """Get financial statement type and range for a page"""
        for fs_type, pages in fs_pages.items():
            if page_num in pages:
                return fs_type, pages
        return "UNKNOWN", [page_num]

    def _map_fs_type_to_section(self, fs_type):
        """Map financial statement type to section type"""
        if 'BALANCE' in fs_type:
            return 'BALANCE_SHEET'
        elif 'PROFIT' in fs_type or 'LOSS' in fs_type:
            return 'INCOME_STATEMENT'
        elif 'CASH' in fs_type:
            return 'CASH_FLOW'
        else:
            return 'OTHER'

    def _smart_split_content(self, content, page_num, balance_sheet_id):
        """Split content smartly using improved regex"""
        chunks = []

        # Split on numbered note headers only (Note 1:, Note 2:, etc.)
        sections = re.split(self.note_pattern, content)

        # Merge small fragments
        merged = []
        current = ""
        for section in sections:
            if len(section.strip()) < 300:
                current += section
            else:
                if current:
                    merged.append(current)
                    current = ""
                merged.append(section)
        if current:
            merged.append(current)

        # Create chunks
        for i, text in enumerate(merged):
            if len(text.strip()) > 50:  # Ignore tiny fragments
                chunks.append({
                    'balance_sheet_id': balance_sheet_id,
                    'content': text.strip(),
                    'section_type': 'NOTES',
                    'page_num': page_num,
                    'chunk_type': 'Narrative',
                    'source_title': f"Note Content - Page {page_num}",
                    'start_page': page_num,
                    'end_page': page_num,
                })

        return chunks

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