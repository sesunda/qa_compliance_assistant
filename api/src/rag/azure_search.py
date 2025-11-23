"""
Azure AI Search implementation for RAG system

🎓 LEARNING CONCEPTS:
1. Vector Search: Store and query high-dimensional embeddings
2. Hybrid Search: Combine keyword (BM25) + vector similarity
3. Metadata Filtering: Filter by framework, category, control ID
4. Index Schema: Define document structure for compliance data
5. Semantic Ranking: AI-powered relevance reranking (optional)
"""

from typing import List, Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SimpleField,
    SearchableField,
)
from azure.search.documents.models import VectorizedQuery
import asyncio
from api.src.config import settings


class AzureSearchVectorStore:
    """
    Azure AI Search implementation for semantic search
    
    🎓 LEARNING: This class demonstrates:
    - Creating search indexes with vector fields
    - Uploading documents with embeddings
    - Hybrid search (keyword + vector)
    - Metadata filtering for multi-framework queries
    """
    
    def __init__(self):
        """
        Initialize Azure AI Search clients
        
        🎓 LEARNING: Two clients needed:
        1. SearchIndexClient: Manages index schema (create/update indexes)
        2. SearchClient: Queries and uploads documents
        """
        if not settings.AZURE_SEARCH_ENABLED:
            return
            
        # Import LLM service for embeddings
        from .llm_service import llm_service
        self.llm_service = llm_service
        
        # Create credentials
        credential = AzureKeyCredential(settings.AZURE_SEARCH_API_KEY)
        
        # Index management client (for schema operations)
        self.index_client = SearchIndexClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )
        
        # Search client (for queries and uploads)
        self.search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            credential=credential
        )
        
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        self.embedding_dimensions = 1536  # OpenAI ada-002 / text-embedding-3-small
    
    def _create_index_schema(self) -> SearchIndex:
        """
        Define the search index schema
        
        🎓 LEARNING - Index Schema Design:
        
        1. SIMPLE FIELDS (filterable, sortable, facetable):
           - id: Unique document identifier
           - framework: ISO27001, NIST CSF, IM8 (for filtering)
           - category: access_control, asset_management, etc.
        
        2. SEARCHABLE FIELDS (full-text search):
           - title: Control title (keyword search)
           - content: Control description (main search target)
        
        3. VECTOR FIELD (semantic search):
           - content_vector: 1536-dimensional embedding
           - Uses HNSW algorithm for fast approximate search
        
        4. WHY THIS STRUCTURE?
           - Enables: "Show me ISO27001 access control requirements"
           - Combines: Framework filter + category filter + semantic search
        """
        
        # Define all fields in the index
        fields = [
            # Identity and metadata fields
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,  # Primary key - must be unique
                filterable=True
            ),
            SimpleField(
                name="framework",
                type=SearchFieldDataType.String,
                filterable=True,  # Enable: framework eq 'ISO 27001'
                facetable=True    # Enable: Count documents per framework
            ),
            SimpleField(
                name="category",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            
            # Text fields for keyword search
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,  # Included in full-text search
                analyzer_name="en.microsoft"  # English language analyzer
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="en.microsoft"
            ),
            
            # Vector field for semantic search
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,  # Vector searchable
                vector_search_dimensions=self.embedding_dimensions,
                vector_search_profile_name="compliance-vector-profile"
            ),
        ]
        
        # Configure vector search algorithm
        # 🎓 LEARNING - HNSW Algorithm:
        # - Hierarchical Navigable Small World graphs
        # - Fast approximate nearest neighbor search
        # - Trades perfect accuracy for speed (99%+ accuracy, 100x faster)
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    parameters={
                        "m": 4,  # Number of connections per node
                        "efConstruction": 400,  # Build-time accuracy
                        "efSearch": 500,  # Query-time accuracy
                        "metric": "cosine"  # Distance metric for embeddings
                    }
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="compliance-vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ]
        )
        
        # Create the index
        return SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
    
    async def create_index(self):
        """
        Create the search index if it doesn't exist
        
        🎓 LEARNING: Index creation is idempotent
        - Check if exists before creating
        - Schema can be updated later (with limitations)
        """
        try:
            # Check if index already exists
            existing_index = self.index_client.get_index(self.index_name)
            print(f"✓ Index '{self.index_name}' already exists")
            return existing_index
        except:
            # Create new index
            print(f"Creating new index: {self.index_name}")
            index = self._create_index_schema()
            result = self.index_client.create_index(index)
            print(f"✓ Index '{self.index_name}' created successfully")
            return result
    
    async def upload_documents(self, documents: List[Dict[str, Any]]):
        """
        Upload documents with embeddings to Azure AI Search
        
        🎓 LEARNING - Document Upload Process:
        1. Generate embeddings for each document's content
        2. Prepare document with all fields including vector
        3. Batch upload (more efficient than one-by-one)
        4. Azure AI Search automatically indexes for both keyword & vector search
        
        Args:
            documents: List of dicts with id, title, content, framework, category
        """
        if not documents:
            return
        
        # Prepare documents with embeddings
        search_documents = []
        for doc in documents:
            # Generate embedding for content
            text = f"{doc['title']} {doc['content']}"
            embedding = await self.llm_service.get_embedding(text)
            
            # Prepare document for upload
            search_doc = {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "framework": doc["framework"],
                "category": doc["category"],
                "content_vector": embedding  # 1536-dimensional vector
            }
            search_documents.append(search_doc)
        
        # Upload documents in batch
        # 🎓 LEARNING: Batch operations are more efficient
        # - Upload up to 1000 documents per batch
        # - Returns success/failure status for each document
        result = self.search_client.upload_documents(documents=search_documents)
        
        succeeded = sum(1 for r in result if r.succeeded)
        print(f"✓ Uploaded {succeeded}/{len(documents)} documents to Azure AI Search")
        
        return result
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        framework_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search documents using hybrid or vector-only search
        
        🎓 LEARNING - Search Modes:
        
        1. VECTOR-ONLY SEARCH (semantic understanding):
           - Query: "How do I secure passwords?"
           - Matches: "Authentication requirements", "Credential management"
           - Uses: Cosine similarity between query & document embeddings
        
        2. KEYWORD SEARCH (exact matches):
           - Query: "ISO 27001 A.9.4.3"
           - Matches: Exact control ID
           - Uses: BM25 algorithm (like search engines)
        
        3. HYBRID SEARCH (best of both):
           - Combines vector + keyword scores
           - Better recall: Finds documents missed by either method alone
           - Recommended for production
        
        Args:
            query: User's search query
            top_k: Number of results to return
            framework_filter: Filter by framework (e.g., "ISO 27001")
            category_filter: Filter by category (e.g., "access_control")
            hybrid: Use hybrid search (True) or vector-only (False)
        
        Returns:
            List of matching documents with scores
        """
        # Generate query embedding for vector search
        query_embedding = await self.llm_service.get_embedding(query)
        
        # Create vector query
        # 🎓 LEARNING: VectorizedQuery tells Azure AI Search:
        # - Which field to search (content_vector)
        # - What vector to compare against (query_embedding)
        # - How many results to retrieve (k_nearest_neighbors)
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector"
        )
        
        # Build filter string for metadata filtering
        # 🎓 LEARNING: OData filter syntax
        # - Combine multiple conditions with 'and'
        # - String equality: field eq 'value'
        filters = []
        if framework_filter:
            filters.append(f"framework eq '{framework_filter}'")
        if category_filter:
            filters.append(f"category eq '{category_filter}'")
        
        filter_string = " and ".join(filters) if filters else None
        
        # Execute search
        # 🎓 LEARNING: Search parameters
        # - search_text: Keyword search query (None = vector-only)
        # - vector_queries: List of vector queries
        # - filter: OData filter expression
        # - top: Maximum results
        # - select: Fields to return
        results = self.search_client.search(
            search_text=query if hybrid else None,  # Keyword search
            vector_queries=[vector_query],  # Vector search
            filter=filter_string,
            top=top_k,
            select=["id", "title", "content", "framework", "category"]
        )
        
        # Process results
        # 🎓 LEARNING: Search scores
        # - @search.score: Relevance score (higher = better match)
        # - Hybrid: Combined keyword + vector score
        # - Vector-only: Cosine similarity score
        documents = []
        for result in results:
            doc = {
                "id": result["id"],
                "title": result["title"],
                "content": result["content"],
                "framework": result["framework"],
                "category": result["category"],
                "similarity_score": result["@search.score"],  # Relevance score
                "search_type": "hybrid" if hybrid else "vector"
            }
            documents.append(doc)
        
        return documents
    
    async def get_document_count(self) -> int:
        """Get total number of documents in the index"""
        try:
            stats = self.index_client.get_index_statistics(self.index_name)
            return stats["document_count"]
        except:
            return 0


# Global instance (only created if Azure Search is enabled)
azure_search_store = AzureSearchVectorStore() if settings.AZURE_SEARCH_ENABLED else None
