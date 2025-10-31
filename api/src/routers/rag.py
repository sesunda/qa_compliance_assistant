"""RAG API endpoints for AI-powered compliance assistance"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.src.database import get_db
from api.src.auth import get_current_user
from api.src.models import User
from api.src.rag.hybrid_rag import hybrid_rag

router = APIRouter(prefix="/rag", tags=["RAG System"])


class RAGQuery(BaseModel):
    query: str
    search_type: Optional[str] = "hybrid"  # vector, graph, hybrid
    max_results: Optional[int] = 5


class RAGResponse(BaseModel):
    query: str
    answer: str
    search_type: str
    sources: List[Dict[str, Any]]
    source_count: int


class DocumentUpload(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"
    framework: Optional[str] = "custom"


@router.post("/ask", response_model=RAGResponse)
async def ask_rag_question(
    request: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question using the RAG system"""
    
    try:
        # Validate search type
        if request.search_type not in ["vector", "graph", "hybrid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="search_type must be one of: vector, graph, hybrid"
            )
        
        # Process the query
        response = await hybrid_rag.ask(
            query=request.query,
            search_type=request.search_type
        )
        
        return RAGResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )


@router.post("/search")
async def search_knowledge_base(
    request: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search the knowledge base without generating an AI answer"""
    
    try:
        # Validate search type
        if request.search_type not in ["vector", "graph", "hybrid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="search_type must be one of: vector, graph, hybrid"
            )
        
        # Perform search
        response = await hybrid_rag.search(
            query=request.query,
            search_type=request.search_type,
            top_k=request.max_results
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching knowledge base: {str(e)}"
        )


@router.post("/upload-document")
async def upload_document(
    document: DocumentUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document to the knowledge base"""
    
    try:
        # Check permissions
        if not current_user.role.permissions.get("system", {}).get("manage_knowledge"):
            # Allow admins and analysts to upload documents
            allowed_roles = ["super_admin", "admin", "analyst"]
            if current_user.role.name not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to upload documents"
                )
        
        # Create document object
        doc_obj = {
            "id": f"CUSTOM_{len(hybrid_rag.vector_store.documents) + 1:03d}",
            "title": document.title,
            "content": document.content,
            "category": document.category,
            "framework": document.framework,
            "uploaded_by": current_user.username
        }
        
        # Add to knowledge base
        hybrid_rag.add_document(doc_obj)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": doc_obj["id"],
            "title": document.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about the knowledge base"""
    
    try:
        documents = hybrid_rag.vector_store.documents
        
        # Calculate statistics
        total_docs = len(documents)
        frameworks = {}
        categories = {}
        
        for doc in documents:
            framework = doc.get("framework", "Unknown")
            category = doc.get("category", "Unknown")
            
            frameworks[framework] = frameworks.get(framework, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        # Knowledge graph stats
        graph = hybrid_rag.knowledge_graph.graph
        graph_stats = {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "node_types": {}
        }
        
        for node_id, data in graph.nodes(data=True):
            node_type = data.get("type", "Unknown")
            graph_stats["node_types"][node_type] = graph_stats["node_types"].get(node_type, 0) + 1
        
        return {
            "vector_store": {
                "total_documents": total_docs,
                "frameworks": frameworks,
                "categories": categories
            },
            "knowledge_graph": graph_stats,
            "last_updated": "2024-01-15T10:00:00Z"  # Could be dynamic
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting knowledge base stats: {str(e)}"
        )


@router.get("/examples")
async def get_example_queries(
    current_user: User = Depends(get_current_user)
):
    """Get example queries for the RAG system"""
    
    examples = [
        {
            "category": "Controls",
            "queries": [
                "What are the key ISO 27001 access control requirements?",
                "How do I implement encryption controls?",
                "What monitoring controls are recommended?",
                "Explain asset management best practices"
            ]
        },
        {
            "category": "Compliance",
            "queries": [
                "What evidence is needed for SOC 2 compliance?",
                "How often should risk assessments be performed?",
                "What are the NIST Cybersecurity Framework categories?",
                "Explain compliance audit procedures"
            ]
        },
        {
            "category": "Implementation",
            "queries": [
                "How to implement incident response procedures?",
                "What are vulnerability management best practices?",
                "How to establish a security awareness program?",
                "Steps for implementing patch management"
            ]
        },
        {
            "category": "Risk Management",
            "queries": [
                "How to conduct a risk assessment?",
                "What is risk treatment methodology?",
                "How to document risk acceptance decisions?",
                "Explain risk monitoring procedures"
            ]
        }
    ]
    
    return {
        "examples": examples,
        "search_types": [
            {
                "type": "vector",
                "description": "Semantic similarity search using AI embeddings"
            },
            {
                "type": "graph", 
                "description": "Knowledge graph-based concept relationships"
            },
            {
                "type": "hybrid",
                "description": "Combined vector and graph search for comprehensive results"
            }
        ]
    }