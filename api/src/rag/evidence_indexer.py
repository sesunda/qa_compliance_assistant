"""
Evidence Indexer - Index Evidence Content to Azure Search

Processes uploaded evidence files and indexes their content
for semantic search capabilities.

Pipeline:
1. Extract text from evidence file (PDF, DOCX, TXT)
2. Split into chunks
3. Generate embeddings
4. Upload to Azure Search index
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from api.src.config import settings

logger = logging.getLogger(__name__)


class EvidenceIndexer:
    """
    Index evidence file contents for semantic search
    
    Creates searchable chunks from evidence documents
    with full metadata linking back to source evidence.
    """
    
    INDEX_NAME = "evidence-content"
    
    def __init__(self):
        """Initialize evidence indexer"""
        self.azure_search_enabled = settings.AZURE_SEARCH_ENABLED
        self.search_client = None
        self.index_client = None
        self.llm_service = None
        
        if self.azure_search_enabled:
            self._init_azure_clients()
    
    def _init_azure_clients(self):
        """Initialize Azure Search clients"""
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            from azure.search.documents.indexes import SearchIndexClient
            
            credential = AzureKeyCredential(settings.AZURE_SEARCH_API_KEY)
            
            self.index_client = SearchIndexClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                credential=credential
            )
            
            self.search_client = SearchClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=self.INDEX_NAME,
                credential=credential
            )
            
            # Import LLM service for embeddings
            from .llm_service import llm_service
            self.llm_service = llm_service
            
            logger.info(f"✅ Evidence indexer initialized with Azure Search index: {self.INDEX_NAME}")
            
        except ImportError as e:
            logger.warning(f"⚠️ Azure Search SDK not installed: {e}")
            self.azure_search_enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Search: {e}")
            self.azure_search_enabled = False
    
    async def create_index(self):
        """Create the evidence-content search index if it doesn't exist"""
        if not self.azure_search_enabled or not self.index_client:
            logger.warning("Azure Search not enabled, skipping index creation")
            return False
        
        try:
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
            
            # Check if index exists
            try:
                existing = self.index_client.get_index(self.INDEX_NAME)
                logger.info(f"✓ Index '{self.INDEX_NAME}' already exists")
                return True
            except:
                pass  # Index doesn't exist, create it
            
            # Define index schema
            fields = [
                # Primary key: combination of evidence_id and chunk_index
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                
                # Evidence metadata
                SimpleField(
                    name="evidence_id",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    sortable=True
                ),
                SimpleField(
                    name="control_id",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                SimpleField(
                    name="project_id",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                SimpleField(
                    name="agency_id",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                
                # Document metadata
                SearchableField(
                    name="evidence_title",
                    type=SearchFieldDataType.String,
                    searchable=True
                ),
                SimpleField(
                    name="file_name",
                    type=SearchFieldDataType.String,
                    filterable=True
                ),
                SimpleField(
                    name="evidence_type",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                
                # Chunk metadata
                SimpleField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    sortable=True
                ),
                SimpleField(
                    name="page_number",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                
                # Content
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
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="evidence-vector-profile"
                ),
                
                # Timestamps
                SimpleField(
                    name="indexed_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True
                ),
            ]
            
            # Vector search configuration
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-config",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="evidence-vector-profile",
                        algorithm_configuration_name="hnsw-config"
                    )
                ]
            )
            
            # Create index
            index = SearchIndex(
                name=self.INDEX_NAME,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_index(index)
            logger.info(f"✅ Created Azure Search index: {self.INDEX_NAME}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create evidence index: {e}", exc_info=True)
            return False
    
    async def index_evidence(
        self,
        evidence_id: int,
        file_path: str,
        evidence_metadata: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Index an evidence file's content
        
        Args:
            evidence_id: Database ID of the evidence record
            file_path: Path to the evidence file
            evidence_metadata: Metadata about the evidence (control_id, title, etc.)
            db: Optional database session for updating indexed status
            
        Returns:
            Dict with indexing results
        """
        from .document_processor import document_processor
        from .chunker import text_chunker
        
        result = {
            "success": False,
            "evidence_id": evidence_id,
            "chunks_indexed": 0,
            "error": None
        }
        
        try:
            # Step 1: Extract text from document
            logger.info(f"📄 Extracting text from evidence {evidence_id}: {file_path}")
            extraction = await document_processor.extract_text(file_path)
            
            if not extraction["success"]:
                result["error"] = f"Text extraction failed: {extraction.get('error')}"
                logger.warning(result["error"])
                return result
            
            text = extraction["text"]
            if not text or len(text.strip()) < 10:
                result["error"] = "Extracted text is too short or empty"
                logger.warning(result["error"])
                return result
            
            # Step 2: Chunk the text
            logger.info(f"✂️ Chunking text ({len(text)} chars) for evidence {evidence_id}")
            
            # Check if we have page information
            pages = extraction["metadata"].get("pages")
            if pages:
                chunks = text_chunker.chunk_pages(pages, metadata=evidence_metadata)
            else:
                chunks = text_chunker.chunk_text(text, metadata=evidence_metadata)
            
            if not chunks:
                result["error"] = "No chunks generated from text"
                logger.warning(result["error"])
                return result
            
            logger.info(f"✅ Created {len(chunks)} chunks for evidence {evidence_id}")
            
            # Step 3: Generate embeddings and upload to Azure Search
            if self.azure_search_enabled and self.search_client:
                indexed_count = await self._upload_chunks(
                    evidence_id=evidence_id,
                    chunks=chunks,
                    evidence_metadata=evidence_metadata
                )
                result["chunks_indexed"] = indexed_count
                result["success"] = indexed_count > 0
            else:
                # Store in memory or log for non-Azure mode
                result["chunks_indexed"] = len(chunks)
                result["success"] = True
                logger.info(f"📝 Azure Search disabled - {len(chunks)} chunks prepared but not uploaded")
            
            # Step 4: Update evidence record with indexed timestamp
            if db and result["success"]:
                try:
                    from api.src.models import Evidence
                    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
                    if evidence:
                        # Add indexed_at if column exists, or use a flag
                        # For now, just log success
                        logger.info(f"✅ Evidence {evidence_id} indexed successfully")
                except Exception as e:
                    logger.warning(f"Could not update evidence record: {e}")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Failed to index evidence {evidence_id}: {e}", exc_info=True)
            return result
    
    async def _upload_chunks(
        self,
        evidence_id: int,
        chunks: List[Dict[str, Any]],
        evidence_metadata: Dict[str, Any]
    ) -> int:
        """Upload chunks with embeddings to Azure Search"""
        
        if not self.search_client or not self.llm_service:
            return 0
        
        documents = []
        
        for chunk in chunks:
            try:
                # Generate embedding for chunk content
                embedding = await self.llm_service.get_embedding(chunk["text"])
                
                # Create search document
                doc_id = f"ev{evidence_id}_chunk{chunk['chunk_index']}"
                
                search_doc = {
                    "id": doc_id,
                    "evidence_id": evidence_id,
                    "control_id": evidence_metadata.get("control_id"),
                    "project_id": evidence_metadata.get("project_id"),
                    "agency_id": evidence_metadata.get("agency_id"),
                    "evidence_title": evidence_metadata.get("title", ""),
                    "file_name": evidence_metadata.get("file_name", ""),
                    "evidence_type": evidence_metadata.get("evidence_type", ""),
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk.get("metadata", {}).get("page_number"),
                    "content": chunk["text"],
                    "content_vector": embedding,
                    "indexed_at": datetime.utcnow().isoformat() + "Z"
                }
                
                documents.append(search_doc)
                
            except Exception as e:
                logger.error(f"Failed to process chunk {chunk['chunk_index']}: {e}")
                continue
        
        if not documents:
            return 0
        
        # Upload to Azure Search
        try:
            result = self.search_client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(f"✅ Uploaded {succeeded}/{len(documents)} chunks to Azure Search")
            return succeeded
        except Exception as e:
            logger.error(f"❌ Failed to upload chunks to Azure Search: {e}")
            return 0
    
    async def search_evidence_content(
        self,
        query: str,
        control_id: Optional[int] = None,
        project_id: Optional[int] = None,
        agency_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search across evidence file contents
        
        Args:
            query: Search query
            control_id: Optional filter by control
            project_id: Optional filter by project
            agency_id: Optional filter by agency (for multi-tenancy)
            top_k: Number of results
            
        Returns:
            List of matching evidence chunks with metadata
        """
        if not self.azure_search_enabled or not self.search_client:
            logger.warning("Azure Search not enabled for evidence content search")
            return []
        
        try:
            from azure.search.documents.models import VectorizedQuery
            
            # Generate query embedding
            query_embedding = await self.llm_service.get_embedding(query)
            
            # Build filter
            filters = []
            if control_id:
                filters.append(f"control_id eq {control_id}")
            if project_id:
                filters.append(f"project_id eq {project_id}")
            if agency_id:
                filters.append(f"agency_id eq {agency_id}")
            
            filter_string = " and ".join(filters) if filters else None
            
            # Create vector query
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # Execute search
            results = self.search_client.search(
                search_text=query,  # Hybrid search
                vector_queries=[vector_query],
                filter=filter_string,
                top=top_k,
                select=[
                    "id", "evidence_id", "control_id", "project_id",
                    "evidence_title", "file_name", "evidence_type",
                    "chunk_index", "page_number", "content"
                ]
            )
            
            # Process results
            documents = []
            for result in results:
                doc = {
                    "id": result["id"],
                    "evidence_id": result["evidence_id"],
                    "control_id": result["control_id"],
                    "project_id": result["project_id"],
                    "evidence_title": result["evidence_title"],
                    "file_name": result["file_name"],
                    "evidence_type": result["evidence_type"],
                    "chunk_index": result["chunk_index"],
                    "page_number": result.get("page_number"),
                    "content": result["content"],
                    "score": result["@search.score"]
                }
                documents.append(doc)
            
            logger.info(f"✅ Found {len(documents)} evidence chunks for query: {query[:50]}...")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Evidence content search failed: {e}", exc_info=True)
            return []
    
    async def delete_evidence_chunks(self, evidence_id: int) -> bool:
        """Delete all chunks for an evidence item (when evidence is deleted)"""
        if not self.azure_search_enabled or not self.search_client:
            return True
        
        try:
            # Search for all chunks with this evidence_id
            results = self.search_client.search(
                search_text="*",
                filter=f"evidence_id eq {evidence_id}",
                select=["id"]
            )
            
            # Collect document IDs to delete
            doc_ids = [{"id": result["id"]} for result in results]
            
            if doc_ids:
                self.search_client.delete_documents(documents=doc_ids)
                logger.info(f"✅ Deleted {len(doc_ids)} chunks for evidence {evidence_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete evidence chunks: {e}")
            return False
    
    async def backfill_evidence(self, db: Session) -> Dict[str, Any]:
        """
        Backfill all existing evidence from database to Azure Search
        
        Args:
            db: Database session
            
        Returns:
            Dict with backfill results
        """
        if not self.azure_search_enabled:
            logger.info("Azure Search disabled, skipping backfill")
            return {"success": False, "message": "Azure Search not enabled"}
        
        try:
            from api.src.models import Evidence
            
            # Get all evidence with uploaded files
            evidence_list = db.query(Evidence).filter(
                Evidence.original_filename.isnot(None),
                Evidence.file_path.isnot(None)
            ).all()
            
            logger.info(f"🔄 Backfilling {len(evidence_list)} evidence items to Azure Search...")
            
            indexed = 0
            failed = 0
            errors = []
            
            for evidence in evidence_list:
                try:
                    # Need to load file content from storage
                    file_content = None
                    if evidence.file_path:
                        # Read file from storage
                        from api.src.file_utils import read_file_from_storage
                        file_content = await read_file_from_storage(evidence.file_path)
                    
                    if file_content:
                        # Index this evidence
                        await self.index_evidence(
                            evidence_id=evidence.id,
                            file_content=file_content,
                            file_name=evidence.original_filename,
                            db=db
                        )
                        indexed += 1
                        logger.info(f"✅ Indexed evidence {evidence.id}: {evidence.original_filename}")
                    else:
                        failed += 1
                        errors.append(f"Evidence {evidence.id}: No file content found")
                        logger.warning(f"⚠️ Skipped evidence {evidence.id}: No file content")
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Evidence {evidence.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"❌ Failed to index evidence {evidence.id}: {e}")
            
            result = {
                "success": True,
                "total": len(evidence_list),
                "indexed": indexed,
                "failed": failed,
                "errors": errors[:10]  # Limit to first 10 errors
            }
            
            logger.info(f"✅ Backfill complete: {indexed}/{len(evidence_list)} evidence indexed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Backfill failed: {e}", exc_info=True)
            return {
                "success": False,
                "total": 0,
                "indexed": 0,
                "failed": 0,
                "error": str(e)
            }


# Global instance
evidence_indexer = EvidenceIndexer()
