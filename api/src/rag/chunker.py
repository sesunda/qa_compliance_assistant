"""
Text Chunker for Document Indexing

Splits large documents into smaller chunks suitable for:
- Embedding generation (token limits)
- Semantic search (focused context)
- RAG retrieval (relevant snippets)

Features:
- Configurable chunk size and overlap
- Token-based splitting (using tiktoken)
- Preserves sentence boundaries when possible
- Tracks chunk metadata (position, page, etc.)
"""

import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Split text into chunks for embedding and indexing
    
    Strategies:
    1. Token-based: Split by token count (best for LLM context)
    2. Sentence-based: Split at sentence boundaries
    3. Paragraph-based: Split at paragraph boundaries
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        tokenizer: str = "cl100k_base"  # GPT-4 / text-embedding-3 tokenizer
    ):
        """
        Initialize chunker with configuration
        
        Args:
            chunk_size: Target tokens per chunk (default: 500)
            chunk_overlap: Overlap tokens between chunks (default: 50)
            tokenizer: Tiktoken encoding name
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer_name = tokenizer
        self.tokenizer = None
        
        self._init_tokenizer()
    
    def _init_tokenizer(self):
        """Initialize tiktoken tokenizer"""
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding(self.tokenizer_name)
            logger.info(f"✅ Tokenizer initialized: {self.tokenizer_name}")
        except ImportError:
            logger.warning("⚠️ tiktoken not installed. Using word-based chunking. Install: pip install tiktoken")
            self.tokenizer = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to load tokenizer: {e}. Using word-based chunking.")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate tokens as words * 1.3
            return int(len(text.split()) * 1.3)
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks
        
        Args:
            text: Full text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with:
            - text: Chunk content
            - chunk_index: Position in document
            - token_count: Tokens in chunk
            - char_start: Character start position
            - char_end: Character end position
            - metadata: Inherited metadata
        """
        if not text or not text.strip():
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        char_position = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence exceeds chunk size, split it further
            if sentence_tokens > self.chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(self._create_chunk(
                        text=chunk_text,
                        index=len(chunks),
                        char_start=char_position - len(chunk_text),
                        metadata=metadata
                    ))
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence into smaller pieces
                sub_chunks = self._split_long_text(sentence)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk(
                        text=sub_chunk,
                        index=len(chunks),
                        char_start=char_position,
                        metadata=metadata
                    ))
                    char_position += len(sub_chunk) + 1
                continue
            
            # Check if adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(self._create_chunk(
                    text=chunk_text,
                    index=len(chunks),
                    char_start=char_position - len(chunk_text),
                    metadata=metadata
                ))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences
                current_tokens = sum(self.count_tokens(s) for s in overlap_sentences)
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
            char_position += len(sentence) + 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(self._create_chunk(
                text=chunk_text,
                index=len(chunks),
                char_start=char_position - len(chunk_text),
                metadata=metadata
            ))
        
        logger.info(f"✅ Created {len(chunks)} chunks from {len(text)} characters")
        
        return chunks
    
    def chunk_pages(
        self,
        pages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk document with page information preserved
        
        Args:
            pages: List of page dicts with 'page' and 'text' keys
            metadata: Optional metadata to attach
            
        Returns:
            Chunks with page numbers tracked
        """
        all_chunks = []
        
        for page_info in pages:
            page_num = page_info.get("page", 0)
            page_text = page_info.get("text", "")
            
            if not page_text.strip():
                continue
            
            # Add page number to metadata
            page_metadata = {**(metadata or {}), "page_number": page_num}
            
            # Chunk this page
            page_chunks = self.chunk_text(page_text, page_metadata)
            
            all_chunks.extend(page_chunks)
        
        # Re-index chunks sequentially
        for i, chunk in enumerate(all_chunks):
            chunk["chunk_index"] = i
        
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting on . ! ? followed by space and capital
        # More sophisticated: use nltk or spacy
        
        # Pattern: split on sentence-ending punctuation followed by space
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(pattern, text)
        
        # Filter empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_long_text(self, text: str) -> List[str]:
        """Split text that exceeds chunk size into smaller pieces"""
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            chunks = []
            
            for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
                chunk_tokens = tokens[i:i + self.chunk_size]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)
            
            return chunks
        else:
            # Word-based fallback
            words = text.split()
            chunks = []
            chunk_size_words = int(self.chunk_size / 1.3)  # Approximate words from tokens
            
            for i in range(0, len(words), chunk_size_words):
                chunk = " ".join(words[i:i + chunk_size_words])
                chunks.append(chunk)
            
            return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap from end of chunk"""
        if not sentences:
            return []
        
        overlap_sentences = []
        overlap_tokens = 0
        
        # Take sentences from the end until we hit overlap limit
        for sentence in reversed(sentences):
            tokens = self.count_tokens(sentence)
            if overlap_tokens + tokens > self.chunk_overlap:
                break
            overlap_sentences.insert(0, sentence)
            overlap_tokens += tokens
        
        return overlap_sentences
    
    def _create_chunk(
        self,
        text: str,
        index: int,
        char_start: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create chunk dictionary"""
        return {
            "text": text,
            "chunk_index": index,
            "token_count": self.count_tokens(text),
            "char_count": len(text),
            "char_start": max(0, char_start),
            "char_end": max(0, char_start) + len(text),
            "metadata": metadata or {}
        }


# Global instance with default settings
text_chunker = TextChunker(
    chunk_size=500,
    chunk_overlap=50
)
