"""
AI Task Orchestrator - Connects AI Assistant with Agent Task System

This service allows the AI assistant to automatically create and execute
agent tasks based on natural language user requests.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from api.src.models import AgentTask, User
from api.src.agent_schemas import AgentTaskCreate

logger = logging.getLogger(__name__)


class AITaskOrchestrator:
    """Orchestrates AI-driven agent task creation and execution"""
    
    def __init__(self):
        self.intent_patterns = {
            'upload_evidence': [
                'upload evidence',
                'add evidence',
                'submit evidence',
                'attach evidence',
                'provide evidence',
                'evidence for',
                'uploading an evidence',
                'attached file',
                'upload document',
                'submit document',
                'upload file',
                'attach file',
                'submit file'
            ],
            'fetch_evidence': [
                'fetch evidence',
                'download evidence',
                'get evidence',
                'retrieve evidence',
                'collect evidence'
            ],
            'analyze_compliance': [
                'analyze compliance',
                'check compliance',
                'compliance analysis',
                'compliance status',
                'how compliant',
                'compliance score'
            ],
            'generate_report': [
                'generate report',
                'create report',
                'compliance report',
                # Removed 'audit report' to avoid conflict with evidence uploads
                'assessment report',
                'generate compliance report',
                'create compliance report'
            ]
        }
    
    def detect_intent(self, user_message: str, has_file: bool = False) -> Optional[str]:
        """
        Detect user intent from natural language message
        
        Args:
            user_message: User's natural language input
            has_file: Whether a file was uploaded with the message
            
        Returns:
            Detected intent (task_type) or None
        """
        message_lower = user_message.lower()
        
        # If a file is uploaded, prioritize upload_evidence intent
        if has_file:
            # Check if message contains evidence/document upload keywords
            upload_indicators = ['evidence', 'document', 'report', 'audit', 'assessment', 'upload', 'attach']
            if any(indicator in message_lower for indicator in upload_indicators):
                logger.info(f"Detected intent 'upload_evidence' due to file upload with keywords")
                return 'upload_evidence'
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    logger.info(f"Detected intent '{intent}' from pattern '{pattern}'")
                    return intent
        
        return None
    
    def extract_control_from_message(self, user_message: str, db: Session) -> Optional[int]:
        """
        Extract control ID from user message by matching keywords to control names
        
        Args:
            user_message: User's natural language input
            db: Database session
            
        Returns:
            Control ID if matched, None otherwise
        """
        from api.src.models import Control
        
        message_lower = user_message.lower()
        
        # Get all active controls
        controls = db.query(Control).filter(Control.status == 'active').all()
        
        # Control keyword matching patterns
        control_keywords = {
            'mfa': ['mfa', 'multi-factor', 'multi factor', '2fa', 'two-factor', 'authentication'],
            'network': ['network', 'segmentation', 'firewall', 'network security'],
            'encryption': ['encrypt', 'encryption', 'crypto', 'data at rest', 'encrypted'],
            'access': ['access control', 'access management', 'identity', 'iam'],
        }
        
        # Try to match control by keywords
        for control in controls:
            control_name_lower = control.name.lower()
            
            # Direct name match
            if any(word in message_lower for word in control_name_lower.split()):
                logger.info(f"Matched control by name: {control.name} (ID: {control.id})")
                return control.id
            
            # Keyword matching
            for keyword_group, keywords in control_keywords.items():
                if keyword_group in control_name_lower or any(kw in control_name_lower for kw in keywords):
                    if any(kw in message_lower for kw in keywords):
                        logger.info(f"Matched control by keywords: {control.name} (ID: {control.id})")
                        return control.id
        
        return None
    
    def extract_entities(self, user_message: str, intent: str, db: Session = None) -> Dict[str, Any]:
        """
        Extract entities (parameters) from user message
        
        Args:
            user_message: User's natural language input
            intent: Detected intent/task type
            db: Database session (optional, for control matching)
            
        Returns:
            Dictionary of extracted parameters
        """
        entities = {}
        message_lower = user_message.lower()
        
        # Extract project ID
        if 'project' in message_lower:
            # Simple pattern matching - in production, use NER
            words = message_lower.split()
            for i, word in enumerate(words):
                if word in ['project', 'project_id', 'proj']:
                    if i + 1 < len(words) and words[i + 1].isdigit():
                        entities['project_id'] = int(words[i + 1])
        
        # Extract control ID (explicit)
        if 'control' in message_lower:
            words = message_lower.split()
            for i, word in enumerate(words):
                if word in ['control', 'control_id']:
                    if i + 1 < len(words) and words[i + 1].isdigit():
                        entities['control_id'] = int(words[i + 1])
        
        # Intelligent control matching (if db provided and control_id not explicitly set)
        if db and 'control_id' not in entities and intent in ['fetch_evidence', 'upload_evidence']:
            matched_control_id = self.extract_control_from_message(user_message, db)
            if matched_control_id:
                entities['control_id'] = matched_control_id
        
        # Extract framework
        frameworks = ['im8', 'iso27001', 'iso', 'nist']
        for framework in frameworks:
            if framework in message_lower:
                if framework == 'iso':
                    entities['framework'] = 'ISO27001'
                else:
                    entities['framework'] = framework.upper()
                break
        
        # Set defaults based on intent
        if intent == 'analyze_compliance':
            entities.setdefault('project_id', 1)
            entities.setdefault('framework', 'IM8')
            entities.setdefault('include_evidence', True)
            entities.setdefault('generate_recommendations', True)
        
        elif intent == 'fetch_evidence':
            entities.setdefault('project_id', 1)
            entities.setdefault('created_by', 1)
            entities.setdefault('control_id', 1)
        
        return entities
    
    def create_task_payload(
        self, 
        intent: str, 
        entities: Dict[str, Any],
        file_path: Optional[str] = None,
        current_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create task payload based on intent and extracted entities
        
        Args:
            intent: Task type/intent
            entities: Extracted parameters
            file_path: Optional file path for evidence
            current_user_id: ID of the user creating the task (for maker-checker)
            
        Returns:
            Task payload dictionary
        """
        if intent == 'analyze_compliance':
            return {
                'project_id': entities.get('project_id', 1),
                'framework': entities.get('framework', 'IM8'),
                'include_evidence': entities.get('include_evidence', True),
                'generate_recommendations': entities.get('generate_recommendations', True)
            }
        
        elif intent in ['fetch_evidence', 'upload_evidence']:
            # Both fetch_evidence and upload_evidence use the same payload structure
            sources = []
            
            # Use current_user_id for proper maker-checker attribution
            creator_id = current_user_id or entities.get('created_by', 1)
            
            # If file path provided, use it
            if file_path:
                sources.append({
                    'type': 'file',
                    'location': file_path,
                    'description': entities.get('description', 'Evidence uploaded via AI assistant'),
                    'control_id': entities.get('control_id', 1)
                })
            else:
                # Use default test file
                sources.append({
                    'type': 'file',
                    'location': '/app/storage/test_evidence/test_doc.txt',
                    'description': 'Default test evidence',
                    'control_id': entities.get('control_id', 1)
                })
            
            return {
                'sources': sources,
                'project_id': entities.get('project_id', 1),
                'created_by': creator_id  # Use actual user ID for maker-checker
            }
        
        elif intent == 'generate_report':
            return {
                'project_id': entities.get('project_id', 1),
                'report_type': entities.get('report_type', 'compliance'),
                'framework': entities.get('framework', 'IM8')
            }
        
        else:
            return {}
    
    def generate_task_description(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        Generate human-readable task description
        
        Args:
            intent: Task type
            entities: Task parameters
            
        Returns:
            Task description string
        """
        if intent == 'analyze_compliance':
            framework = entities.get('framework', 'IM8')
            project_id = entities.get('project_id', 1)
            return f"AI-initiated compliance analysis for project {project_id} using {framework} framework"
        
        elif intent in ['fetch_evidence', 'upload_evidence']:
            control_id = entities.get('control_id', 1)
            return f"AI-initiated evidence upload for control {control_id}"
        
        elif intent == 'generate_report':
            return "AI-initiated compliance report generation"
        
        else:
            return "AI-initiated task"
    
    async def create_task_from_message(
        self,
        user_message: str,
        db: Session,
        current_user: Dict[str, Any],  # Changed from User to Dict
        file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Main orchestration method: detect intent and create task
        
        Args:
            user_message: User's natural language input
            db: Database session
            current_user: Current user dict (from auth)
            file_path: Optional file path for evidence uploads
            
        Returns:
            Dictionary with task info and response message, or None if no intent detected
        """
        # Detect intent (pass has_file flag)
        has_file = file_path is not None
        intent = self.detect_intent(user_message, has_file=has_file)
        if not intent:
            return None
        
        # Map upload_evidence to fetch_evidence (they use the same handler)
        # The fetch_evidence handler can handle both fetching remote evidence
        # and processing uploaded evidence files
        task_type = 'fetch_evidence' if intent == 'upload_evidence' else intent
        
        # Extract entities (pass db for intelligent control matching)
        entities = self.extract_entities(user_message, intent, db=db)
        
        # Create payload with current user ID for maker-checker
        payload = self.create_task_payload(
            intent, 
            entities, 
            file_path,
            current_user_id=current_user.get("id") if isinstance(current_user, dict) else current_user.id
        )
        
        # Create task
        task_create = AgentTaskCreate(
            task_type=task_type,  # Use mapped task_type
            title=f"AI Assistant: {intent.replace('_', ' ').title()}",
            description=self.generate_task_description(intent, entities),
            payload=payload
        )
        
        # Save to database
        db_task = AgentTask(
            task_type=task_create.task_type,
            title=task_create.title,
            description=task_create.description,
            payload=task_create.payload,
            status="pending",
            progress=0,
            created_by=current_user.get("id") if isinstance(current_user, dict) else current_user.id
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        logger.info(f"Created task {db_task.id} from AI message: {intent} (task_type: {task_type})")
        
        return {
            'task_id': db_task.id,
            'task_type': task_type,  # Return the mapped task_type
            'message': self._generate_response_message(intent, db_task.id, entities),
            'task': db_task
        }
    
    def _generate_response_message(
        self, 
        intent: str, 
        task_id: int, 
        entities: Dict[str, Any]
    ) -> str:
        """Generate AI assistant response message"""
        
        if intent == 'analyze_compliance':
            framework = entities.get('framework', 'IM8')
            project_id = entities.get('project_id', 1)
            return f"✅ I've created a compliance analysis task (ID: {task_id}) for project {project_id} using the {framework} framework. The agent will analyze all controls and provide a detailed compliance score with recommendations. You can monitor the task progress in the Agent Tasks section."
        
        elif intent == 'fetch_evidence' or intent == 'upload_evidence':
            control_id = entities.get('control_id', 1)
            return f"✅ I've created an evidence collection task (ID: {task_id}) for control {control_id}. The agent will process and verify your document with SHA-256 checksums for integrity verification. The evidence will be securely stored and linked to the control. You can track the progress in Agent Tasks."
        
        elif intent == 'generate_report':
            return f"✅ I've created a report generation task (ID: {task_id}). The agent will compile a comprehensive compliance report. Check Agent Tasks for progress."
        
        else:
            return f"✅ Task {task_id} created and queued for execution."


# Singleton instance
ai_task_orchestrator = AITaskOrchestrator()
