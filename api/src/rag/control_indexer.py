"""
Control Indexer - Sync Database Controls to Azure Search

Indexes control requirements from the database to enable
semantic search across all controls in a project.

Features:
- Index new controls on creation
- Update index when controls are modified
- Backfill existing controls
- Multi-tenant filtering by agency
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from api.src.config import settings

logger = logging.getLogger(__name__)


class ControlIndexer:
    """
    Index database controls for semantic search
    
    Syncs control requirements from PostgreSQL to Azure Search
    enabling natural language queries like "show MFA controls"
    """
    
    # Use the main compliance-knowledge index
    INDEX_NAME = "compliance-knowledge"
    
    def __init__(self):
        """Initialize control indexer"""
        self.azure_search_enabled = settings.AZURE_SEARCH_ENABLED
        self.search_client = None
        self.llm_service = None
        
        if self.azure_search_enabled:
            self._init_azure_clients()
    
    def _init_azure_clients(self):
        """Initialize Azure Search clients"""
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            
            credential = AzureKeyCredential(settings.AZURE_SEARCH_API_KEY)
            
            self.search_client = SearchClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=self.INDEX_NAME,
                credential=credential
            )
            
            # Import LLM service for embeddings
            from .llm_service import llm_service
            self.llm_service = llm_service
            
            logger.info(f"✅ Control indexer initialized with Azure Search index: {self.INDEX_NAME}")
            
        except ImportError as e:
            logger.warning(f"⚠️ Azure Search SDK not installed: {e}")
            self.azure_search_enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Search: {e}")
            self.azure_search_enabled = False
    
    async def index_control(
        self,
        control_id: int,
        name: str,
        description: str,
        project_id: int,
        agency_id: int,
        control_type: Optional[str] = None,
        framework: str = "IM8"
    ) -> Dict[str, Any]:
        """
        Index a single control to Azure Search
        
        Args:
            control_id: Database ID of the control
            name: Control name/title
            description: Control description/requirements
            project_id: Associated project ID
            agency_id: Agency ID for multi-tenancy
            control_type: Type of control
            framework: Compliance framework (IM8, ISO27001, etc.)
            
        Returns:
            Dict with indexing result
        """
        result = {
            "success": False,
            "control_id": control_id,
            "error": None
        }
        
        if not self.azure_search_enabled or not self.search_client:
            logger.info(f"📝 Azure Search disabled - control {control_id} not indexed")
            result["success"] = True  # Not an error, just not indexed
            return result
        
        try:
            # Combine name and description for embedding
            text = f"{name}\n\n{description or ''}"
            
            # Generate embedding
            embedding = await self.llm_service.get_embedding(text)
            
            # Create document ID with prefix to distinguish from static docs
            doc_id = f"db_control_{control_id}"
            
            # Determine category from control type or name
            category = self._determine_category(name, control_type)
            
            # Create search document
            search_doc = {
                "id": doc_id,
                "title": name,
                "content": description or name,
                "framework": framework,
                "category": category,
                "content_vector": embedding
            }
            
            # Upload to Azure Search
            upload_result = self.search_client.upload_documents(documents=[search_doc])
            
            if upload_result and upload_result[0].succeeded:
                logger.info(f"✅ Indexed control {control_id}: {name[:50]}...")
                result["success"] = True
            else:
                result["error"] = "Upload failed"
                logger.warning(f"⚠️ Failed to index control {control_id}")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Failed to index control {control_id}: {e}", exc_info=True)
            return result
    
    async def index_controls_batch(
        self,
        controls: List[Dict[str, Any]],
        framework: str = "IM8"
    ) -> Dict[str, Any]:
        """
        Index multiple controls in batch
        
        Args:
            controls: List of control dicts with id, name, description, project_id, agency_id
            framework: Compliance framework
            
        Returns:
            Dict with batch results
        """
        result = {
            "success": False,
            "total": len(controls),
            "indexed": 0,
            "failed": 0,
            "errors": []
        }
        
        if not self.azure_search_enabled or not self.search_client:
            logger.info(f"📝 Azure Search disabled - {len(controls)} controls not indexed")
            result["success"] = True
            return result
        
        documents = []
        
        for control in controls:
            try:
                control_id = control["id"]
                name = control["name"]
                description = control.get("description", "")
                
                # Combine for embedding
                text = f"{name}\n\n{description}"
                embedding = await self.llm_service.get_embedding(text)
                
                doc_id = f"db_control_{control_id}"
                category = self._determine_category(name, control.get("control_type"))
                
                search_doc = {
                    "id": doc_id,
                    "title": name,
                    "content": description or name,
                    "framework": framework,
                    "category": category,
                    "content_vector": embedding
                }
                
                documents.append(search_doc)
                
            except Exception as e:
                result["errors"].append(f"Control {control.get('id')}: {str(e)}")
                result["failed"] += 1
        
        if documents:
            try:
                upload_result = self.search_client.upload_documents(documents=documents)
                succeeded = sum(1 for r in upload_result if r.succeeded)
                result["indexed"] = succeeded
                result["failed"] += len(documents) - succeeded
                result["success"] = succeeded > 0
                
                logger.info(f"✅ Indexed {succeeded}/{len(documents)} controls")
                
            except Exception as e:
                result["errors"].append(f"Batch upload failed: {str(e)}")
                logger.error(f"❌ Batch upload failed: {e}")
        
        return result
    
    async def backfill_controls(self, db: Session) -> Dict[str, Any]:
        """
        Backfill all existing controls from database to Azure Search
        
        Args:
            db: Database session
            
        Returns:
            Dict with backfill results
        """
        from api.src.models import Control
        
        result = {
            "success": False,
            "total": 0,
            "indexed": 0,
            "errors": []
        }
        
        try:
            # Get all controls
            controls = db.query(Control).all()
            result["total"] = len(controls)
            
            if not controls:
                logger.info("No controls found in database")
                result["success"] = True
                return result
            
            logger.info(f"🔄 Backfilling {len(controls)} controls to Azure Search...")
            
            # Convert to dicts
            control_dicts = []
            for control in controls:
                control_dicts.append({
                    "id": control.id,
                    "name": control.name,
                    "description": control.description,
                    "project_id": control.project_id,
                    "agency_id": control.agency_id,
                    "control_type": control.control_type
                })
            
            # Index in batch
            batch_result = await self.index_controls_batch(control_dicts)
            
            result["indexed"] = batch_result["indexed"]
            result["errors"] = batch_result["errors"]
            result["success"] = batch_result["success"]
            
            logger.info(f"✅ Backfill complete: {result['indexed']}/{result['total']} controls indexed")
            
            return result
            
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"❌ Backfill failed: {e}", exc_info=True)
            return result
    
    async def delete_control(self, control_id: int) -> bool:
        """Delete a control from the search index"""
        if not self.azure_search_enabled or not self.search_client:
            return True
        
        try:
            doc_id = f"db_control_{control_id}"
            self.search_client.delete_documents(documents=[{"id": doc_id}])
            logger.info(f"✅ Deleted control {control_id} from search index")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete control {control_id}: {e}")
            return False
    
    def _determine_category(self, name: str, control_type: Optional[str]) -> str:
        """Determine category from control name or type"""
        name_lower = name.lower()
        
        # Category keywords mapping
        categories = {
            "access_control": ["access", "authentication", "authorization", "mfa", "password", "identity", "login"],
            "network_security": ["network", "firewall", "segmentation", "perimeter", "vpn"],
            "data_protection": ["data", "encryption", "backup", "classification", "privacy"],
            "operations_security": ["operations", "monitoring", "logging", "patch", "vulnerability"],
            "incident_response": ["incident", "response", "recovery", "continuity"],
            "compliance": ["compliance", "audit", "policy", "governance"],
            "asset_management": ["asset", "inventory", "configuration"],
            "risk_management": ["risk", "assessment", "threat"]
        }
        
        for category, keywords in categories.items():
            if any(kw in name_lower for kw in keywords):
                return category
        
        # Default based on control_type if provided
        if control_type:
            return control_type.lower().replace(" ", "_")
        
        return "general"


# Global instance
control_indexer = ControlIndexer()
