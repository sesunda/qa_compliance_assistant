"""RAG API endpoints for AI-powered compliance assistance"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.src.database import get_db
from api.src.auth import get_current_user
from api.src.models import User
from api.src.rag.hybrid_rag import hybrid_rag
from api.src.rag.im8_agent import im8_agent
from api.src.services.ai_task_orchestrator import ai_task_orchestrator
from api.src.services.conversation_manager import ConversationManager
from api.src.services.agentic_assistant import AgenticAssistant
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG System"])

# Initialize agentic assistant
agentic_assistant = AgenticAssistant()


class RAGQuery(BaseModel):
    query: str
    search_type: Optional[str] = "hybrid"  # vector, graph, hybrid
    max_results: Optional[int] = 5
    enable_task_execution: Optional[bool] = True  # Enable AI task orchestration
    model_provider: Optional[str] = "groq"  # groq, openai, anthropic, ollama
    session_id: Optional[str] = None  # Conversation session ID for multi-turn
    use_agent: Optional[bool] = True  # Use Groq agentic assistant (default: True)


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


@router.post("/ask")
async def ask_question(
    request: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question using agentic assistant with conversation memory and tool calling"""
    try:
        # Initialize conversation manager
        conv_manager = ConversationManager(db, current_user["id"])
        
        # Get or create session
        session = None
        if request.session_id:
            session = conv_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Create new session for this query
            session = conv_manager.create_session(
                title=request.query[:50] + "..." if len(request.query) > 50 else request.query
            )
        
        # Add user message to conversation
        conv_manager.add_message(
            session.session_id,
            role="user",
            content=request.query
        )
        
        # Use Groq agentic assistant if enabled
        if request.use_agent:
            logger.info(f"Using agentic assistant for session {session.session_id}")
            
            result = await agentic_assistant.chat(
                message=request.query,
                conversation_manager=conv_manager,
                session_id=session.session_id,
                db=db,
                current_user=current_user,
                file_path=None  # TODO: Support file uploads
            )
            
            response = {
                "query": request.query,
                "answer": result["answer"],
                "task_created": len(result.get("tool_calls", [])) > 0,
                "tool_calls": result.get("tool_calls", []),
                "search_type": "agentic",
                "sources": [],
                "source_count": 0,
                "session_id": session.session_id
            }
            
            return response
        
        # Fallback: Keyword-based task execution (legacy)
        task_result = None
        if request.enable_task_execution:
            task_result = await ai_task_orchestrator.create_task_from_message(
                user_message=request.query,
                db=db,
                current_user=current_user,
                file_path=None
            )
        
        # Prepare response
        if task_result:
            # Task was created
            answer = task_result['message']
            
            # Add assistant message to conversation
            conv_manager.add_message(
                session.session_id,
                role="assistant",
                content=answer,
                task_id=task_result['task_id']
            )
            
            # Update context with task info
            conv_manager.update_context(
                session.session_id,
                {
                    "last_task_id": task_result['task_id'],
                    "last_task_type": task_result['task_type']
                }
            )
            
            return {
                "query": request.query,
                "answer": answer,
                "task_created": True,
                "task_id": task_result['task_id'],
                "task_type": task_result['task_type'],
                "search_type": "task_execution",
                "sources": [],
                "source_count": 0,
                "session_id": session.session_id
            }
        
        # Otherwise, proceed with normal RAG response
        response = await hybrid_rag.ask(
            query=request.query,
            search_type=request.search_type
        )
        
        # Add assistant message to conversation
        conv_manager.add_message(
            session.session_id,
            role="assistant",
            content=response.get('answer', '')
        )
        
        # Add task execution info and session
        response['task_created'] = False
        response['session_id'] = session.session_id
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG ask: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/im8-agent")
async def im8_agentic_reasoning(
    request: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Singapore IM8 compliance analysis with agentic reasoning"""
    try:
        # Use the IM8 agent for sophisticated multi-step reasoning
        context = {
            "user_role": getattr(current_user, 'role', 'admin'),
            "agency_context": "Singapore Government",
            "compliance_framework": "IM8"
        }
        
        response = await im8_agent.analyze_compliance_query(
            query=request.query,
            context=context
        )
        
        return response
        
    except Exception as e:
        print(f"Error in IM8 agent reasoning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in agentic reasoning: {str(e)}"
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


@router.get("/provider-info")
async def get_provider_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the current LLM provider"""
    
    try:
        provider_info = hybrid_rag.get_provider_info()
        return {
            "current_provider": provider_info,
            "free_options": {
                "groq": {
                    "description": "Fast inference with generous free tier",
                    "free_tier": "30 requests/minute, 6000 requests/day", 
                    "models": ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
                    "setup": "Set GROQ_API_KEY environment variable"
                },
                "ollama": {
                    "description": "Run models locally, completely free",
                    "free_tier": "Unlimited (local)",
                    "models": ["llama2", "codellama", "mistral", "phi"],
                    "setup": "Install Ollama locally and set OLLAMA_BASE_URL"
                },
                "anthropic": {
                    "description": "High quality responses with free tier",
                    "free_tier": "Limited free credits",
                    "models": ["claude-3-haiku-20240307"],
                    "setup": "Set ANTHROPIC_API_KEY environment variable"
                }
            },
            "setup_instructions": {
                "groq": [
                    "1. Go to https://console.groq.com/",
                    "2. Create account and get API key",
                    "3. Set GROQ_API_KEY environment variable",
                    "4. Restart the API service"
                ],
                "ollama": [
                    "1. Install Ollama from https://ollama.ai/",
                    "2. Run 'ollama run llama2' to download model",
                    "3. Set LLM_PROVIDER=ollama in config",
                    "4. Restart the API service"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting provider info: {str(e)}"
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


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio to text using Groq Whisper API
    Supports multi-modal input for voice-to-text
    """
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use Groq's Whisper API for transcription
            from groq import Groq
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GROQ_API_KEY not configured for speech-to-text"
                )
            
            client = Groq(api_key=groq_api_key)
            
            # Open the audio file and transcribe
            with open(temp_file_path, 'rb') as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=("recording.webm", audio_file.read()),
                    model="whisper-large-v3",
                    response_format="json",
                    language="en",  # Can be made dynamic
                    temperature=0.0  # Deterministic output
                )
            
            return {
                "success": True,
                "text": transcription.text,
                "language": "en",
                "model": "whisper-large-v3"
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech-to-text transcription failed: {str(e)}"
        )


@router.post("/ask-with-file")
async def ask_with_file(
    query: str = Form(...),
    search_type: str = Form("hybrid"),
    enable_task_execution: bool = Form(True),
    model_provider: str = Form("groq"),
    use_agent: bool = Form(True),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question with optional file upload for evidence
    Supports multi-modal input with document upload and conversation memory
    """
    try:
        # Initialize conversation manager
        conv_manager = ConversationManager(db, current_user["id"])
        
        # Get or create session
        session = None
        if session_id:
            session = conv_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Create new session for this query
            session = conv_manager.create_session(
                title=query[:50] + "..." if len(query) > 50 else query
            )
        
        # Add user message to conversation
        conv_manager.add_message(
            session.session_id,
            role="user",
            content=query
        )
        
        file_path = None
        
        # If file is uploaded, save it
        if file:
            import hashlib
            from datetime import datetime
            
            # Create storage directory
            storage_dir = "/app/storage/evidence"
            os.makedirs(storage_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(storage_dir, safe_filename)
            
            # Save file
            content = await file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved uploaded file to {file_path}")
        
        # Use Groq agentic assistant if enabled
        if use_agent:
            logger.info(f"Using agentic assistant for file upload in session {session.session_id}")
            
            result = await agentic_assistant.chat(
                message=query,
                conversation_manager=conv_manager,
                session_id=session.session_id,
                db=db,
                current_user=current_user,
                file_path=file_path
            )
            
            return {
                "query": query,
                "answer": result["answer"],
                "task_created": len(result.get("tool_calls", [])) > 0,
                "tool_calls": result.get("tool_calls", []),
                "search_type": "agentic",
                "sources": [],
                "source_count": 0,
                "file_uploaded": file_path is not None,
                "file_path": file_path,
                "session_id": session.session_id
            }
        
        # Fallback: Legacy keyword-based task execution
        task_result = None
        if enable_task_execution:
            # If file is uploaded but no clear intent in query, default to upload_evidence
            query_to_use = query
            if file and not any(keyword in query.lower() for keyword in ['analyze', 'report', 'fetch', 'download']):
                # Enhance query to trigger upload_evidence intent
                if 'upload' not in query.lower() and 'evidence' not in query.lower():
                    query_to_use = f"Upload evidence document: {query}"
            
            task_result = await ai_task_orchestrator.create_task_from_message(
                user_message=query_to_use,
                db=db,
                current_user=current_user,
                file_path=file_path
            )
        
        # If a task was created, return task creation response
        if task_result:
            # Add assistant message to conversation
            conv_manager.add_message(
                session.session_id,
                role="assistant",
                content=task_result['message'],
                task_id=task_result['task_id']
            )
            
            # Update context with task info
            conv_manager.update_context(
                session.session_id,
                {
                    "last_task_id": task_result['task_id'],
                    "last_task_type": task_result['task_type']
                }
            )
            
            return {
                "query": query,
                "answer": task_result['message'],
                "task_created": True,
                "task_id": task_result['task_id'],
                "task_type": task_result['task_type'],
                "search_type": "task_execution",
                "sources": [],
                "source_count": 0,
                "file_uploaded": file_path is not None,
                "file_path": file_path,
                "session_id": session.session_id
            }
        
        # Otherwise, proceed with normal RAG response
        response = await hybrid_rag.ask(
            query=query,
            search_type=search_type
        )
        
        # Add task execution info
        response['task_created'] = False
        response['file_uploaded'] = file_path is not None
        
        return response
        
    except Exception as e:
        logger.error(f"Error in ask_with_file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )