"""Embedding service for RAG using Gemini text-embedding-004 model."""
from django.conf import settings
from typing import List, Tuple
import math

# Try new google-genai library first, fallback to old one
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

EMBEDDING_MODEL = "text-embedding-004"


class EmbeddingService:
    """Service for creating embeddings using Gemini text-embedding-004."""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            self.client = None
            self.use_new_api = False
            return
        
        if USE_NEW_GENAI is True:
            try:
                self.client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
                self.use_new_api = True
            except Exception:
                self.client = None
                self.use_new_api = False
        else:
            try:
                if google_genai:
                    google_genai.configure(api_key=settings.GEMINI_API_KEY)
                self.use_new_api = False
            except Exception:
                self.client = None
                self.use_new_api = False
    
    def create_embedding(self, text: str) -> list:
        """Create embedding for text using text-embedding-004."""
        if not self.client and not self.use_new_api:
            return []
        
        if not text or not text.strip():
            return []
        
        try:
            if self.use_new_api and self.client:
                response = self.client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text
                )
                
                if hasattr(response, 'embeddings') and response.embeddings:
                    raw_embedding = response.embeddings[0]
                    embedding_vector = self._extract_embedding_vector(raw_embedding)
                    
                    if embedding_vector:
                        return [float(x) for x in embedding_vector]
                    return []
                    
                elif hasattr(response, 'embedding'):
                    raw_embedding = response.embedding
                    if isinstance(raw_embedding, (list, tuple)):
                        return [float(x) for x in raw_embedding]
                    else:
                        return [float(x) for x in list(raw_embedding)]
                else:
                    return []
            else:
                return []
                
        except APIError:
            return []
        except Exception:
            return []
    
    def _extract_embedding_vector(self, raw_embedding):
        """Extract embedding vector from various response structures."""
        if hasattr(raw_embedding, 'values'):
            values = raw_embedding.values
            if isinstance(values, (list, tuple)):
                return [float(x) for x in values]
            else:
                return [float(x) for x in list(values)]
        elif hasattr(raw_embedding, 'embedding'):
            embedding = raw_embedding.embedding
            return [float(x) for x in list(embedding)]
        elif isinstance(raw_embedding, (list, tuple)):
            if raw_embedding and isinstance(raw_embedding[0], (list, tuple)):
                return [float(x) for sublist in raw_embedding for x in sublist]
            else:
                return [float(x) for x in raw_embedding]
        else:
            try:
                if hasattr(raw_embedding, '__iter__') and not isinstance(raw_embedding, (str, bytes)):
                    try:
                        return [float(x) for x in raw_embedding]
                    except (TypeError, ValueError):
                        embedding_vector = []
                        for item in raw_embedding:
                            if isinstance(item, (list, tuple)):
                                embedding_vector.extend([float(x) for x in item])
                            else:
                                embedding_vector.append(float(item))
                        return embedding_vector
                else:
                    temp_list = list(raw_embedding)
                    if temp_list and isinstance(temp_list[0], tuple):
                        return [float(x) for tup in temp_list for x in tup]
                    else:
                        return [float(x) for x in temp_list]
            except (TypeError, ValueError, AttributeError):
                return []
    
    def create_embeddings_batch(self, texts: list) -> list:
        """Create embeddings for multiple texts (batch processing)."""
        embeddings = []
        for text in texts:
            embedding = self.create_embedding(text)
            embeddings.append(embedding)
        return embeddings


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    if len(vec1) != len(vec2):
        return 0.0
    
    try:
        dot_product = sum(float(a) * float(b) for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(float(a) * float(a) for a in vec1))
        magnitude2 = math.sqrt(sum(float(b) * float(b) for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    except (TypeError, ValueError):
        return 0.0
