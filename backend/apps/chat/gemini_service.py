import google.generativeai as genai
from django.conf import settings
from apps.balance_sheets.chunk_retriever import ChunkRetriever
from apps.balance_sheets.models import BalanceSheet, FinancialData


class GeminiChatService:
    """Service for generating AI responses using Gemini with RAG context."""
    
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def analyze_company_performance(self, query, company_data, use_chunks=True):
        """
        Main entry point for generating AI responses.
        Orchestrates context building, prompt creation, and response generation.
        """
        if not self.model:
            return "Gemini API is not configured. Please set GEMINI_API_KEY in settings."
        
        try:
            # Build context from RAG chunks or financial data
            context = self._build_context(query, company_data, use_chunks)
            
            # Create prompt with context
            prompt = self._create_prompt(query, context)
            
            # Generate response from LLM
            response = self._generate_response(prompt)
            
            # Handle blocked responses
            if self._is_response_blocked(response):
                return self._handle_blocked_response(query, context)
            
            # Extract and clean response text
            response_text = self._extract_response_text(response)
            
            if response_text:
                return self._clean_response(response_text)
            
            return "Sorry, I couldn't generate a response. Please try asking about specific balance sheet metrics."
        
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    def _build_context(self, query, company_data, use_chunks):
        """Build context from RAG chunks or structured financial data."""
        if not use_chunks:
            return self._prepare_financial_context(company_data)
        
        chunk_retriever = ChunkRetriever()
        relevant_chunks = chunk_retriever.get_relevant_chunks(query, company_data, use_vector_search=True)
        
        if relevant_chunks:
            return chunk_retriever.format_chunks_for_context(relevant_chunks)
        
        return self._prepare_financial_context(company_data)
    
    def _create_prompt(self, query, context):
        """Create a well-structured prompt for the LLM."""
        return f"""Based on the financial documents provided below, answer the user's question.

FINANCIAL CONTEXT:
{context}

QUESTION: {query}

INSTRUCTIONS:
- Extract only information that appears in the financial context above
- Provide specific numbers with their units (e.g., ₹ X crore, ₹ Y lakh)
- If asking about "latest year", use the most recent period mentioned
- If the information is not in the context, state "Information not found in the provided documents"
- Keep the answer factual and concise (2-3 sentences maximum)

ANSWER:"""
    
    def _generate_response(self, prompt):
        """Generate response from Gemini LLM with error handling."""
        try:
            return self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 0.7,
                    "top_k": 10,
                }
            )
        except Exception:
            # Fallback with minimal config
            try:
                return self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.0}
                )
            except Exception:
                return None
    
    def _is_response_blocked(self, response):
        """Check if response was blocked by safety filters."""
        if not response:
            return False
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                return candidate.finish_reason == 2  # 2 = SAFETY
        
        return False
    
    def _handle_blocked_response(self, query, context):
        """Handle responses blocked by safety filters."""
        # Try ultra-neutral prompt
        alternative_response = self._retry_with_ultra_neutral_prompt(query, context)
        if alternative_response and self._is_valid_response(alternative_response):
            return alternative_response
        
        # Last resort: pattern extraction (but prefer RAG+LLM)
        direct_answer = self._extract_direct_from_context(query, context)
        if direct_answer and self._is_valid_response(direct_answer):
            return direct_answer
        
        return "I'm having trouble processing your question due to content filtering. Please try rephrasing your question or ensure the balance sheet data has been properly uploaded."
    
    def _extract_response_text(self, response):
        """Extract text from response object using multiple methods."""
        if not response:
            return None
        
        # Method 1: Direct text access
        try:
            if hasattr(response, 'text'):
                return response.text
        except Exception:
            pass
        
        # Method 2: Candidates structure
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    return candidate.content.parts[0].text
                elif hasattr(candidate.content, 'text'):
                    return candidate.content.text
        
        # Method 3: Alternative structure
        try:
            if hasattr(response, 'result') and response.result:
                if hasattr(response.result, 'text'):
                    return response.result.text
        except Exception:
            pass
        
        return None
    
    def _clean_response(self, response_text):
        """Clean up response text by removing verbose patterns."""
        import re
        
        if not response_text:
            return response_text
        
        text = response_text.strip()
        
        # Remove verbose prefixes
        verbose_patterns = [
            r"^As an expert financial analyst.*?(:|,|\.)",
            r"^As a financial analyst.*?(:|,|\.)",
            r"^Based on the financial data.*?(:|,|\.)",
            r"^I have reviewed.*?(:|,|\.)",
            r"^According to.*?(:|,|\.)",
            r"^I must highlight.*?(:|,|\.)",
            r"^I understand your question.*?(:|,|\.)",
        ]
        
        for pattern in verbose_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL).strip()
        
        # Filter out verbose lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not any(line.startswith(word) for word in ['However', 'Therefore', 'While', 'Although', 'Additionally', 'Furthermore']):
                if '₹' in line or ':' in line or len(line) < 200:
                    cleaned_lines.append(line)
        
        if cleaned_lines:
            text = '\n'.join(cleaned_lines).strip()
        
        # Limit to 2 lines if multiple numeric lines
        lines = text.split('\n')
        if len(lines) > 2 and '₹' in text:
            numeric_lines = [l for l in lines if '₹' in l or any(char.isdigit() for char in l)]
            if numeric_lines:
                text = '\n'.join(numeric_lines[:2]).strip()
            else:
                text = '\n'.join(lines[:2]).strip()
        
        return text
    
    def _retry_with_ultra_neutral_prompt(self, query, context):
        """Retry with ultra-neutral prompt format to avoid safety filters."""
        try:
            ultra_neutral_prompt = f"""Extract requested data from documents:

DOCUMENTS:
{context[:3000]}

REQUEST: {query}

RESPONSE FORMAT: Numbers and facts only. If not found, write "Not found in documents".

RESPONSE:"""
            
            response = self.model.generate_content(
                ultra_neutral_prompt,
                generation_config={"temperature": 0.0, "max_output_tokens": 150}
            )
            
            # Check if blocked
            if self._is_response_blocked(response):
                return None
            
            response_text = self._extract_response_text(response)
            
            if response_text and len(response_text) > 10:
                return response_text.strip()
            
            return None
            
        except Exception:
            return None
    
    def _extract_direct_from_context(self, query, context):
        """Extract information directly from context using pattern matching."""
        import re
        
        if not context or "No financial data" in context or ("No relevant" in context and len(context) < 100):
            return "No financial data available. Please upload balance sheet data first."
        
        query_lower = query.lower()
        
        # Extract from structured financial data
        if 'Period:' in context:
            result = self._extract_from_structured_data(query_lower, context)
            if result:
                return result
        
        # Extract from RAG chunks
        if 'current assets' in query_lower:
            result = self._extract_current_assets(query_lower, context)
            if result:
                return result
        
        # Extract goodwill amortization
        if ('goodwill' in query_lower and 'amortization' in query_lower) or \
           ('amortization' in query_lower and 'goodwill' in context.lower()):
            result = self._extract_goodwill_amortization(context)
            if result:
                return result
        
        return f"I couldn't extract that specific information. The data may need to be uploaded or the question rephrased."
    
    def _extract_from_structured_data(self, query_lower, context):
        """Extract from structured Period: format."""
        import re
        
        patterns = {
            'total assets': (r'Total Assets:\s*([\d,\.]+|N/A)', 'Total Assets'),
            'revenue': (r'Revenue:\s*([\d,\.]+|N/A)', 'Revenue'),
            'total liabilities': (r'Total Liabilities:\s*([\d,\.]+|N/A)', 'Total Liabilities'),
            'total equity': (r'Total Equity:\s*([\d,\.]+|N/A)', 'Total Equity'),
            'current assets': (r'Current Assets:\s*([\d,\.]+|N/A)', 'Current Assets'),
            'current ratio': (r'Current Ratio:\s*([\d,\.]+|N/A)', 'Current Ratio'),
            'debt': (r'Debt-to-Equity:\s*([\d,\.]+|N/A)', 'Debt-to-Equity'),
        }
        
        matched_pattern = None
        metric_name = None
        for key, (pattern, name) in patterns.items():
            if key in query_lower:
                matched_pattern = pattern
                metric_name = name
                break
        
        if not matched_pattern:
            return None
        
        sections = re.split(r'Period:\s*', context)
        sections = [s for s in sections if s.strip()]
        
        results = []
        for section in sections[:3]:
            period_match = re.match(r'([^\n]+)', section)
            if not period_match:
                continue
            
            period = period_match.group(1).strip()
            value_match = re.search(matched_pattern, section)
            if not value_match:
                continue
            
            value = value_match.group(1).strip()
            if value == 'N/A' or not value:
                continue
            
            try:
                num_value = float(value.replace(',', ''))
                formatted = self._format_currency(num_value)
                
                if 'as at' not in period and 'March' not in period:
                    year_match = re.search(r'(\d{4})', period)
                    if year_match:
                        period = f"as at 31st March {year_match.group(1)}"
                
                results.append(f"{metric_name} ({period}): {formatted}")
            except ValueError:
                results.append(f"{metric_name} ({period}): ₹ {value}")
        
        return '\n'.join(results) if results else None
    
    def _extract_current_assets(self, query_lower, context):
        """Extract Current Assets from RAG context."""
        import re
        
        patterns = [
            r'(?:\[Page\s+\d+\].*?(?:Balance\s+Sheet|Consolidated|Statement).*?)?Current\s+Assets[^\d]*?([\d]{1,3}(?:[,\d]{3})*(?:\.[\d]+)?)',
            r'(?:^|\n|\.|,|;|\[)\s*Current\s+Assets[:\s]*[^\d]*?([\d,\.]+)',
            r'Current\s+Assets\s+([\d]{1,3}(?:[,\d]{3})*(?:\.[\d]+)?)\s+([\d]{1,3}(?:[,\d]{3})*(?:\.[\d]+)?)',
            r'Current\s+Assets.{0,300}?([\d]{1,3}(?:[,\d]{3})*(?:\.[\d]+)?)',
        ]
        
        results = []
        for pattern in patterns:
            matches = list(re.finditer(pattern, context, re.IGNORECASE | re.MULTILINE))
            
            for match in matches[:10]:
                period_str = "Latest"
                
                if len(match.groups()) >= 2 and match.group(2):
                    value_str = match.group(2).strip()
                    year_str_2 = match.group(4) if len(match.groups()) >= 4 else None
                    if year_str_2:
                        period_str = f"Year {year_str_2}"
                else:
                    value_str = match.group(1).strip()
                
                snippet = context[max(0, match.start() - 300):min(len(context), match.end() + 300)]
                
                if period_str == "Latest":
                    year_match = re.search(r'(?:as\s+at|March|31st\s+March)\s*[,:\s]*(\d{4})', snippet, re.IGNORECASE)
                    if not year_match:
                        year_match = re.search(r'\b(20\d{2})\b', snippet)
                    if year_match:
                        period_str = f"Year {year_match.group(1)}"
                
                try:
                    num_str = re.sub(r'[^\d,\.]', '', value_str).replace(',', '')
                    if num_str and num_str.replace('.', '').isdigit():
                        num_value = float(num_str)
                        if num_value < 100:
                            continue
                        
                        formatted = self._format_currency(num_value)
                        result_text = f"Current Assets ({period_str}): {formatted}"
                        if result_text not in results:
                            results.append(result_text)
                except (ValueError, AttributeError):
                    continue
            
            if results:
                break
        
        if results:
            return '\n'.join(results[:2])
        
        return None
    
    def _extract_goodwill_amortization(self, context):
        """Extract goodwill amortization period from context."""
        import re
        
        patterns = [
            r'goodwill[^.]*?(?:amorti[sz]ed|amortization)[^.]*?(\d+)\s*years?',
            r'amortization[^.]*?goodwill[^.]*?(\d+)\s*years?',
            r'goodwill[^.]*?(\d+)\s*years?[^.]*?amorti',
            r'goodwill[^.]*?(?:over|for|period of)\s*(\d+)\s*years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.DOTALL)
            if match:
                years = match.group(1)
                return f"Goodwill is amortized over {years} years according to the Notes to Accounts."
        
        return None
    
    def _prepare_financial_context(self, company_data):
        """Prepare structured financial data context."""
        context_parts = []
        
        for balance_sheet in company_data:
            fd = balance_sheet.financial_data.first()
            
            if fd:
                current_ratio = fd.current_ratio
                if not current_ratio and fd.current_assets and fd.current_liabilities:
                    try:
                        current_ratio = float(fd.current_assets) / float(fd.current_liabilities)
                    except:
                        current_ratio = None
                
                debt_to_equity = fd.debt_to_equity
                if not debt_to_equity and fd.total_liabilities and fd.total_equity:
                    try:
                        debt_to_equity = float(fd.total_liabilities) / float(fd.total_equity)
                    except:
                        debt_to_equity = None
                
                period_label = f"as at 31st March {balance_sheet.year}" if not balance_sheet.quarter else f"{balance_sheet.year} {balance_sheet.quarter}"
                
                context_parts.append(f"""
Period: {period_label}
Total Assets: {fd.total_assets or 'N/A'}
Current Assets: {fd.current_assets or 'N/A'}
Total Liabilities: {fd.total_liabilities or 'N/A'}
Total Equity: {fd.total_equity or 'N/A'}
Revenue: {fd.revenue or fd.sales or 'N/A'}
Current Ratio: {current_ratio if current_ratio else 'N/A'}
Debt-to-Equity: {debt_to_equity if debt_to_equity else 'N/A'}
""")
        
        return '\n'.join(context_parts) if context_parts else "No financial data available."
    
    def _format_currency(self, value):
        """Format currency value in Indian format."""
        if value >= 10000000:
            return f"₹ {value/10000000:.2f} crore".replace('.00 ', ' ')
        elif value >= 100000:
            return f"₹ {value/100000:.2f} lakh".replace('.00 ', ' ')
        else:
            return f"₹ {value:,.0f}"
    
    def _is_valid_response(self, response):
        """Check if response is valid (not error messages)."""
        if not response:
            return False
        response_lower = response.lower()
        invalid_indicators = ['no ', 'couldn\'t', 'not found', 'error', 'failed']
        return not any(indicator in response_lower for indicator in invalid_indicators)
