import json
from typing import List, Set, Tuple
from .models import PDFChunk
from .embedding_service import EmbeddingService, cosine_similarity


class ChunkRetriever:
    """Smart chunk retrieval using RAG with vector similarity search."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    SECTION_KEYWORDS = {
        'BALANCE_SHEET': [
            'asset', 'liabilit', 'equity', 'balance sheet', 'financial position',
            'current asset', 'non-current asset', 'current liabilit', 'non-current liabilit',
            'shareholder', 'stockholder', 'capital', 'reserve'
        ],
        'INCOME_STATEMENT': [
            'revenue', 'sales', 'income', 'profit', 'loss', 'earning', 'ebitda',
            'expense', 'cost', 'p&l', 'profit and loss', 'statement of income',
            'operating income', 'net income', 'gross profit'
        ],
        'CASH_FLOW': [
            'cash flow', 'operating cash', 'investing cash', 'financing cash',
            'cash from operations', 'cash from investing', 'cash from financing'
        ],
        'RATIOS': [
            'ratio', 'roe', 'roa', 'debt to equity', 'current ratio', 'quick ratio',
            'profit margin', 'return on', 'efficiency', 'liquidity'
        ],
        'NOTES': [
            'note', 'disclosure', 'accounting policy', 'contingent', 'commitment'
        ]
    }
    
    def get_relevant_chunks(self, query: str, balance_sheets: List, use_vector_search: bool = True) -> List[PDFChunk]:
        """Retrieve relevant chunks using RAG with vector similarity search."""
        all_chunks = self._get_chunks_for_query(query, balance_sheets)
        
        if not all_chunks:
            return []
        
        # Try vector-based retrieval first
        if use_vector_search and self.embedding_service.client:
            try:
                query_embedding = self.embedding_service.create_embedding(query)
                
                if query_embedding:
                    top_chunks = self._vector_similarity_search(query_embedding, all_chunks, query)
                    if top_chunks:
                        return top_chunks
            except Exception:
                pass
        
        # Fallback to keyword-based search
        return self._keyword_search(query, all_chunks)
    
    def _get_chunks_for_query(self, query: str, balance_sheets: List) -> List[PDFChunk]:
        """Get chunks filtered by query type."""
        query_lower = query.lower()
        balance_sheet_keywords = ['asset', 'liability', 'equity', 'current assets', 'total assets', 'balance sheet']
        is_balance_sheet_query = any(keyword in query_lower for keyword in balance_sheet_keywords)
        
        if is_balance_sheet_query:
            balance_sheet_chunks = list(PDFChunk.objects.filter(
                balance_sheet__in=balance_sheets,
                section_type='BALANCE_SHEET'
            ))
            other_chunks = list(PDFChunk.objects.filter(
                balance_sheet__in=balance_sheets
            ).exclude(section_type='BALANCE_SHEET'))
            return balance_sheet_chunks + other_chunks
        
        return list(PDFChunk.objects.filter(balance_sheet__in=balance_sheets))
    
    def _vector_similarity_search(self, query_embedding: list, all_chunks: List[PDFChunk], query: str) -> List[PDFChunk]:
        """Perform vector similarity search on chunks."""
        scored_chunks = []
        query_lower = query.lower()
        balance_sheet_keywords = ['asset', 'liability', 'equity', 'current assets', 'total assets', 'balance sheet']
        is_balance_sheet_query = any(keyword in query_lower for keyword in balance_sheet_keywords)
        
        for chunk in all_chunks:
            chunk_vector = self._process_embedding(chunk.embedding)
            
            if chunk_vector and len(chunk_vector) > 0:
                if len(chunk_vector) != len(query_embedding):
                    continue
                
                similarity = cosine_similarity(query_embedding, chunk_vector)
                final_score = self._calculate_chunk_score(similarity, chunk, query_lower, is_balance_sheet_query)
                scored_chunks.append((final_score, chunk))
        
        if scored_chunks:
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_k = min(8, len(scored_chunks))
            return [chunk for score, chunk in scored_chunks[:top_k]]
        
        return []
    
    def _process_embedding(self, raw_embedding) -> list:
        """Process embedding from database into float list."""
        if raw_embedding is None:
            return None
        
        if isinstance(raw_embedding, (list, tuple)) and raw_embedding:
            first_elem = raw_embedding[0]
            
            if isinstance(first_elem, (int, float)):
                return [float(x) for x in raw_embedding]
            elif isinstance(first_elem, (list, tuple)):
                return [float(x) for sublist in raw_embedding for x in sublist]
            else:
                try:
                    return [float(x) for x in raw_embedding]
                except (TypeError, ValueError):
                    return None
        
        return None
    
    def _calculate_chunk_score(self, similarity: float, chunk: PDFChunk, query_lower: str, is_balance_sheet_query: bool) -> float:
        """Calculate final score for chunk with boosts."""
        source_title = (chunk.source_title or '').lower()
        chunk_content_lower = (chunk.content or '').lower()
        
        title_boost = 0.1 if any(word in source_title for word in query_lower.split()) else 0.0
        content_boost = 0.05 if any(word in chunk_content_lower for word in query_lower.split() if len(word) > 3) else 0.0
        section_boost = 0.05 if (chunk.section_type == 'BALANCE_SHEET' and is_balance_sheet_query) else 0.0
        
        return similarity + title_boost + content_boost + section_boost
    
    def _keyword_search(self, query: str, all_chunks: List[PDFChunk]) -> List[PDFChunk]:
        """Fallback keyword-based search."""
        query_lower = query.lower()
        query_keywords = query_lower.split()
        
        scored_chunks = []
        for chunk in all_chunks:
            source_title = getattr(chunk, 'source_title', '') or ''
            content_matches = sum(1 for word in query_keywords if word in chunk.content.lower())
            title_matches = sum(2 for word in query_keywords if word in source_title.lower())
            score = content_matches + title_matches
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_k = min(8, len(scored_chunks))
        return [chunk for score, chunk in scored_chunks[:top_k]]
    
    def _identify_relevant_sections(self, query_lower: str) -> Set[str]:
        """Identify which section types are relevant based on query keywords."""
        relevant = set()
        
        for section_type, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    relevant.add(section_type)
                    break
        
        return relevant
    
    def _needs_multiple_periods(self, query_lower: str) -> bool:
        """Check if query requires comparison across multiple periods."""
        comparison_keywords = [
            'compare', 'comparison', 'trend', 'change', 'growth', 'increase', 'decrease',
            'year over year', 'yoy', 'quarter over quarter', 'qoq', 'vs', 'versus',
            'previous', 'last year', 'last quarter', 'difference', 'delta'
        ]
        
        return any(keyword in query_lower for keyword in comparison_keywords)
    
    def format_chunks_for_context(self, chunks: List[PDFChunk]) -> str:
        """Format chunks into context string for LLM consumption."""
        if not chunks:
            return "No relevant financial context found for your specific query."
        
        context_list = []
        total_length = 0
        max_context_length = 8000
        
        for chunk in chunks:
            chunk_type = getattr(chunk, 'chunk_type', chunk.section_type)
            page_num = getattr(chunk, 'page_num', chunk.start_page)
            source_title = chunk.source_title or f"{chunk.section_type}"
            
            content_snippet = chunk.content[:4000]
            header = f"[Page {page_num}] {source_title} ({chunk_type})"
            chunk_text = f"{header}\n{content_snippet}"
            
            if total_length + len(chunk_text) > max_context_length and context_list:
                break
            
            context_list.append(chunk_text)
            total_length += len(chunk_text)
        
        return "\n\n---\n\n".join(context_list)
