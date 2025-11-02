"""Vector search implementation for RAG system"""

import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from api.src.config import settings
from api.src.database import get_db
from sqlalchemy.orm import Session


class VectorStore:
    """Vector store for semantic search using embeddings"""
    
    def __init__(self):
        # Import LLM service here to avoid circular imports
        from .llm_service import llm_service
        self.llm_service = llm_service
        
        self.embeddings_cache = {}
        self.documents = []
        self.document_embeddings = []
        
        # Load default compliance documents
        self._load_compliance_documents()
    
    def _load_compliance_documents(self):
        """Load default compliance knowledge base"""
        
        # ISO 27001 Controls
        iso_controls = [
            {
                "id": "A.5.1.1",
                "title": "Information Security Policy",
                "content": "An information security policy should be defined, approved by management, published and communicated to employees and relevant external parties.",
                "category": "organizational",
                "framework": "ISO 27001"
            },
            {
                "id": "A.8.1.1", 
                "title": "Inventory of Assets",
                "content": "Assets associated with information and information processing facilities should be identified and an inventory of these assets should be drawn up and maintained.",
                "category": "asset_management",
                "framework": "ISO 27001"
            },
            {
                "id": "A.9.1.1",
                "title": "Access Control Policy",
                "content": "An access control policy should be established, documented and reviewed based on business and information security requirements.",
                "category": "access_control",
                "framework": "ISO 27001"
            },
            {
                "id": "A.12.1.1",
                "title": "Documented Operating Procedures",
                "content": "Operating procedures should be documented and made available to all users who need them.",
                "category": "operations_security",
                "framework": "ISO 27001"
            }
        ]
        
        # NIST Framework
        nist_controls = [
            {
                "id": "ID.AM-1",
                "title": "Physical devices and systems are inventoried",
                "content": "Physical devices and systems within the organization are inventoried to establish a baseline for asset management and to enable risk management decisions.",
                "category": "identify",
                "framework": "NIST CSF"
            },
            {
                "id": "PR.AC-1",
                "title": "Identities and credentials are managed",
                "content": "Identities and credentials are issued, managed, verified, revoked, and audited for authorized devices, users and processes.",
                "category": "protect",
                "framework": "NIST CSF"
            },
            {
                "id": "DE.CM-1",
                "title": "Networks are monitored",
                "content": "The network is monitored to detect potential cybersecurity events and verify the effectiveness of protective measures.",
                "category": "detect",
                "framework": "NIST CSF"
            }
        ]
        
        # Compliance best practices
        best_practices = [
            {
                "id": "BP001",
                "title": "Risk Assessment Methodology",
                "content": "Conduct regular risk assessments using standardized methodologies to identify, analyze, and evaluate information security risks. Document findings and implement appropriate risk treatment measures.",
                "category": "risk_management",
                "framework": "Best Practice"
            },
            {
                "id": "BP002", 
                "title": "Evidence Collection and Management",
                "content": "Establish systematic evidence collection procedures for compliance audits. Maintain proper documentation, version control, and secure storage of evidence materials.",
                "category": "evidence_management",
                "framework": "Best Practice"
            },
            {
                "id": "BP003",
                "title": "Incident Response Planning",
                "content": "Develop comprehensive incident response plans that include detection, containment, eradication, recovery, and lessons learned phases. Regularly test and update plans.",
                "category": "incident_response",
                "framework": "Best Practice"
            }
        ]
        
        # Combine all documents
        all_documents = iso_controls + nist_controls + best_practices
        
        # Add to document store
        for doc in all_documents:
            self.documents.append(doc)
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using LLM service"""
        
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Use the multi-provider LLM service
        embedding = await self.llm_service.get_embedding(text)
        self.embeddings_cache[text] = embedding
        return embedding
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embeddings based on text content for demo purposes"""
        import hashlib
        import random
        
        # Use text hash as seed for consistent embeddings
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Generate 1536-dimensional vector (same as OpenAI ada-002)
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        # Normalize vector
        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x/magnitude for x in embedding]
        
        return embedding
    
    async def index_documents(self):
        """Index all documents by generating embeddings"""
        
        if self.document_embeddings:
            return  # Already indexed
        
        for doc in self.documents:
            # Combine title and content for embedding
            text = f"{doc['title']} {doc['content']}"
            embedding = await self.get_embedding(text)
            self.document_embeddings.append(embedding)
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        
        # Ensure documents are indexed
        await self.index_documents()
        
        if not self.document_embeddings:
            return []
        
        # Get query embedding
        query_embedding = await self.get_embedding(query)
        
        # Calculate similarities
        similarities = cosine_similarity(
            [query_embedding], 
            self.document_embeddings
        )[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.7:  # Minimum similarity threshold
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(similarities[idx])
                doc['search_type'] = 'vector'
                results.append(doc)
        
        return results
    
    def add_document(self, document: Dict[str, Any]):
        """Add a new document to the vector store"""
        self.documents.append(document)
        # Clear embeddings cache to force re-indexing
        self.document_embeddings = []


# Global vector store instance
vector_store = VectorStore()