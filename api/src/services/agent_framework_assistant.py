"""
Microsoft Agent Framework-powered Assistant
Replaces custom tool calling with standardized agent framework
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from agent_framework.openai import OpenAIChatClient
from agent_framework import Agent, Tool
from agent_framework.state import PostgresCheckpointSaver

from api.src.config import settings
from api.src.services.ai_task_orchestrator import ai_task_orchestrator

logger = logging.getLogger(__name__)


class AgentFrameworkAssistant:
    """Agent Framework-powered conversational assistant for compliance tasks"""
    
    def __init__(self):
        """Initialize Agent Framework client and agents"""
        
        # Initialize LLM client (GitHub Models or OpenAI)
        if settings.GITHUB_TOKEN:
            logger.info("Using GitHub Models via Agent Framework")
            self.client = OpenAIChatClient(
                base_url="https://models.inference.ai.azure.com",
                api_key=settings.GITHUB_TOKEN,
                model=settings.GITHUB_MODEL
            )
        elif settings.OPENAI_API_KEY:
            logger.info("Using OpenAI via Agent Framework")
            self.client = OpenAIChatClient(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )
        else:
            raise ValueError("Either GITHUB_TOKEN or OPENAI_API_KEY required for Agent Framework")
        
        # Initialize PostgreSQL checkpointer for conversation state
        self.checkpointer = PostgresCheckpointSaver.from_connection_string(
            settings.DATABASE_URL
        )
        
        # Tools are defined as methods and registered dynamically
        self.all_tools = self._register_tools()
        
        # Agents will be created per-request based on user role
        logger.info(f"Agent Framework initialized with {len(self.all_tools)} tools")
    
    def _register_tools(self) -> List[Tool]:
        """Register all compliance tools as Agent Framework Tool objects"""
        
        tools = []
        
        # Tool 1: Upload Evidence
        @Tool.from_function
        async def upload_evidence(
            control_id: int,
            file_path: str,
            title: str,
            evidence_type: str,
            description: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Upload compliance evidence document for a control.
            
            Args:
                control_id: The ID of the control this evidence relates to
                file_path: Path to the uploaded file
                title: Specific, descriptive title for the evidence
                evidence_type: Type of evidence (policy_document, audit_report, 
                              configuration_screenshot, log_file, certificate, 
                              procedure, test_result)
                description: Optional description of the evidence
            
            Returns:
                Dict with status, evidence_id, and message
            """
            return await self._execute_tool_via_orchestrator(
                "upload_evidence",
                {
                    "control_id": control_id,
                    "file_path": file_path,
                    "title": title,
                    "evidence_type": evidence_type,
                    "description": description
                }
            )
        
        tools.append(upload_evidence)
        
        # Tool 2: Fetch Evidence
        @Tool.from_function
        async def fetch_evidence(
            control_id: Optional[int] = None,
            project_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Retrieve compliance evidence for a specific control or project.
            
            Args:
                control_id: The control ID to fetch evidence for
                project_id: The project ID to fetch evidence for
            
            Returns:
                List of evidence records with metadata
            """
            return await self._execute_tool_via_orchestrator(
                "fetch_evidence",
                {
                    "control_id": control_id,
                    "project_id": project_id
                }
            )
        
        tools.append(fetch_evidence)
        
        # Tool 3: Analyze Evidence
        @Tool.from_function
        async def analyze_evidence(
            evidence_id: int,
            control_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Analyze uploaded evidence against control requirements using RAG.
            Validates if evidence satisfies control acceptance criteria.
            
            Args:
                evidence_id: Evidence ID to analyze (must be valid numeric ID)
                control_id: Optional control ID the evidence relates to
            
            Returns:
                Analysis results with quality assessment and recommendations
            """
            return await self._execute_tool_via_orchestrator(
                "analyze_evidence",
                {
                    "evidence_id": evidence_id,
                    "control_id": control_id
                }
            )
        
        tools.append(analyze_evidence)
        
        # Tool 4: Submit for Review
        @Tool.from_function
        async def submit_for_review(
            evidence_id: int,
            comments: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Submit evidence for auditor review and approval.
            Updates evidence status from 'pending' to 'under_review'.
            
            Args:
                evidence_id: Evidence ID to submit
                comments: Optional comments for the auditor
            
            Returns:
                Submission status and confirmation
            """
            return await self._execute_tool_via_orchestrator(
                "submit_for_review",
                {
                    "evidence_id": evidence_id,
                    "comments": comments
                }
            )
        
        tools.append(submit_for_review)
        
        # Tool 5: Generate Report
        @Tool.from_function
        async def generate_report(
            framework: str,
            project_id: Optional[int] = None,
            report_type: str = "compliance"
        ) -> Dict[str, Any]:
            """
            Generate compliance report for a framework or project.
            
            Args:
                framework: Compliance framework (IM8, NIST, ISO27001)
                project_id: Optional project ID for the report
                report_type: Type of report (compliance, gap, executive)
            
            Returns:
                Generated report with download link
            """
            return await self._execute_tool_via_orchestrator(
                "generate_report",
                {
                    "framework": framework,
                    "project_id": project_id,
                    "report_type": report_type
                }
            )
        
        tools.append(generate_report)
        
        # Tool 6: Request Evidence Upload
        @Tool.from_function
        async def request_evidence_upload(
            control_id: int,
            title: str,
            description: Optional[str] = None,
            evidence_type: str = "document"
        ) -> Dict[str, Any]:
            """
            Request evidence upload from analyst when NO file is attached.
            Creates a pending evidence record as placeholder.
            
            Args:
                control_id: Control ID this evidence relates to
                title: Brief title for the evidence
                description: Detailed description of what evidence will be provided
                evidence_type: Type of evidence (default: document)
            
            Returns:
                Created evidence placeholder ID
            """
            return await self._execute_tool_via_orchestrator(
                "request_evidence_upload",
                {
                    "control_id": control_id,
                    "title": title,
                    "description": description,
                    "evidence_type": evidence_type
                }
            )
        
        tools.append(request_evidence_upload)
        
        # Tool 7: Suggest Related Controls
        @Tool.from_function
        async def suggest_related_controls(
            evidence_id: int,
            control_id: int,
            max_suggestions: int = 5
        ) -> Dict[str, Any]:
            """
            Suggest other controls that uploaded evidence might also satisfy.
            This is for evidence reuse workflow after evidence upload.
            
            Args:
                evidence_id: Evidence ID to analyze (from recent upload)
                control_id: Primary control ID (the control this evidence was uploaded for)
                max_suggestions: Maximum number of suggestions to return
            
            Returns:
                List of suggested controls with similarity scores
            """
            return await self._execute_tool_via_orchestrator(
                "suggest_related_controls",
                {
                    "evidence_id": evidence_id,
                    "control_id": control_id,
                    "max_suggestions": max_suggestions
                }
            )
        
        tools.append(suggest_related_controls)
        
        # Tool 8: Submit Evidence for Review
        @Tool.from_function
        async def submit_evidence_for_review(
            evidence_id: int,
            comments: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Submit evidence for auditor review and approval.
            Updates evidence status from 'pending' to 'under_review'.
            
            Args:
                evidence_id: Evidence ID to submit
                comments: Optional comments for the auditor
            
            Returns:
                Submission confirmation
            """
            return await self._execute_tool_via_orchestrator(
                "submit_evidence_for_review",
                {
                    "evidence_id": evidence_id,
                    "comments": comments
                }
            )
        
        tools.append(submit_evidence_for_review)
        
        # Tool 9: Analyze Evidence for Control
        @Tool.from_function
        async def analyze_evidence_for_control(
            control_id: int
        ) -> Dict[str, Any]:
            """
            AI-powered analysis of evidence quality and coverage for a control.
            Provides insights on completeness, quality, gaps, and recommendations.
            
            Args:
                control_id: The control ID to analyze evidence for
            
            Returns:
                Comprehensive analysis with quality score and recommendations
            """
            return await self._execute_tool_via_orchestrator(
                "analyze_evidence_for_control",
                {
                    "control_id": control_id
                }
            )
        
        tools.append(analyze_evidence_for_control)
        
        # Tool 10: Get Evidence by Control
        @Tool.from_function
        async def get_evidence_by_control(
            control_id: int
        ) -> Dict[str, Any]:
            """
            Retrieve all evidence documents for a specific control.
            Returns evidence ID, title, file name, type, upload date, and status.
            
            Args:
                control_id: The control ID to retrieve evidence for
            
            Returns:
                List of evidence documents with metadata
            """
            return await self._execute_tool_via_orchestrator(
                "get_evidence_by_control",
                {
                    "control_id": control_id
                }
            )
        
        tools.append(get_evidence_by_control)
        
        # Tool 11: Get Recent Evidence
        @Tool.from_function
        async def get_recent_evidence(
            limit: int = 10,
            user_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Retrieve recently uploaded evidence documents.
            
            Args:
                limit: Number of recent evidence items to return (default: 10)
                user_id: Optional filter by user ID
            
            Returns:
                List of recent evidence with metadata
            """
            return await self._execute_tool_via_orchestrator(
                "get_recent_evidence",
                {
                    "limit": limit,
                    "user_id": user_id
                }
            )
        
        tools.append(get_recent_evidence)
        
        # Tool 12: Create Project
        @Tool.from_function
        async def create_project(
            name: str,
            description: Optional[str] = None,
            project_type: str = "compliance_assessment",
            start_date: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a new compliance or security project.
            
            Args:
                name: Project name (required)
                description: Project description
                project_type: Type of project (compliance_assessment, security_audit, 
                             risk_management, penetration_test)
                start_date: Project start date in YYYY-MM-DD format
            
            Returns:
                Created project with project_id
            """
            return await self._execute_tool_via_orchestrator(
                "create_project",
                {
                    "name": name,
                    "description": description,
                    "project_type": project_type,
                    "start_date": start_date
                }
            )
        
        tools.append(create_project)
        
        # Tool 13: List Projects
        @Tool.from_function
        async def list_projects(
            limit: int = 10,
            status: str = "all"
        ) -> Dict[str, Any]:
            """
            List all projects for the user's agency.
            
            Args:
                limit: Number of recent projects to return (default: 10)
                status: Filter by project status (active, completed, archived, all)
            
            Returns:
                List of projects with details
            """
            return await self._execute_tool_via_orchestrator(
                "list_projects",
                {
                    "limit": limit,
                    "status": status
                }
            )
        
        tools.append(list_projects)
        
        # Tool 14: Create Controls
        @Tool.from_function
        async def create_controls(
            project_id: int,
            domains: List[int],
            framework: str = "IM8"
        ) -> Dict[str, Any]:
            """
            Create IM8 compliance controls for a project.
            
            Args:
                project_id: Project ID to add controls to (required)
                domains: IM8 domain numbers to include (1-10)
                framework: Compliance framework (default: IM8)
            
            Returns:
                Created controls count and details
            """
            return await self._execute_tool_via_orchestrator(
                "create_controls",
                {
                    "project_id": project_id,
                    "domains": domains,
                    "framework": framework
                }
            )
        
        tools.append(create_controls)
        
        # Tool 15: Search Documents
        @Tool.from_function
        async def search_documents(
            query: str,
            control_id: Optional[int] = None,
            top_k: int = 5
        ) -> Dict[str, Any]:
            """
            Search compliance knowledge base for control requirements, policies,
            best practices, and standards.
            
            Args:
                query: Natural language search query
                control_id: Optional filter by specific control ID
                top_k: Number of results to return
            
            Returns:
                Search results with relevant excerpts and source citations
            """
            return await self._execute_tool_via_orchestrator(
                "search_documents",
                {
                    "query": query,
                    "control_id": control_id,
                    "top_k": top_k
                }
            )
        
        tools.append(search_documents)
        
        # Tool 16: Resolve Control to Evidence
        @Tool.from_function
        async def resolve_control_to_evidence(
            control_id: int
        ) -> Dict[str, Any]:
            """
            Resolve Control ID to available evidence that can be submitted for review.
            Returns list of pending/rejected evidence for that control.
            
            Args:
                control_id: Control ID to find evidence for
            
            Returns:
                List of available evidence for the control
            """
            return await self._execute_tool_via_orchestrator(
                "resolve_control_to_evidence",
                {
                    "control_id": control_id
                }
            )
        
        tools.append(resolve_control_to_evidence)
        
        # Tool 17: MCP Analyze Compliance
        @Tool.from_function
        async def mcp_analyze_compliance(
            project_id: int,
            framework: str = "IM8",
            include_evidence: bool = True,
            generate_recommendations: bool = True
        ) -> Dict[str, Any]:
            """
            Comprehensive compliance analysis using MCP server.
            Calculates overall compliance score, identifies gaps, and generates recommendations.
            
            Args:
                project_id: Project ID to analyze
                framework: Compliance framework (IM8, ISO27001, NIST)
                include_evidence: Include evidence analysis in assessment
                generate_recommendations: Generate AI recommendations for gaps
            
            Returns:
                Comprehensive compliance analysis with scores and recommendations
            """
            return await self._execute_tool_via_orchestrator(
                "mcp_analyze_compliance",
                {
                    "project_id": project_id,
                    "framework": framework,
                    "include_evidence": include_evidence,
                    "generate_recommendations": generate_recommendations
                }
            )
        
        tools.append(mcp_analyze_compliance)
        
        # Tool 18: Create Assessment
        @Tool.from_function
        async def create_assessment(
            project_id: int,
            name: str,
            assessment_type: str,
            framework: str,
            lead_assessor_user_id: int,
            scope_description: Optional[str] = None,
            team_members: Optional[List[int]] = None,
            planned_start_date: Optional[str] = None,
            planned_end_date: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a comprehensive security or compliance assessment.
            
            Args:
                project_id: Project ID this assessment belongs to
                name: Assessment name
                assessment_type: Type (compliance, risk, security_audit, penetration_test, gap_analysis)
                framework: Compliance framework (IM8, ISO27001, NIST, SOC2, FISMA)
                lead_assessor_user_id: User ID of the lead assessor
                scope_description: Detailed scope and boundaries
                team_members: Array of team member user IDs
                planned_start_date: Planned start date (YYYY-MM-DD)
                planned_end_date: Planned end date (YYYY-MM-DD)
            
            Returns:
                Created assessment with assessment_id
            """
            return await self._execute_tool_via_orchestrator(
                "create_assessment",
                {
                    "project_id": project_id,
                    "name": name,
                    "assessment_type": assessment_type,
                    "framework": framework,
                    "lead_assessor_user_id": lead_assessor_user_id,
                    "scope_description": scope_description,
                    "team_members": team_members,
                    "planned_start_date": planned_start_date,
                    "planned_end_date": planned_end_date
                }
            )
        
        tools.append(create_assessment)
        
        # Tool 19: Create Finding
        @Tool.from_function
        async def create_finding(
            assessment_id: int,
            project_id: int,
            title: str,
            description: str,
            severity: str,
            cvss_score: Optional[float] = None,
            category: Optional[str] = None,
            affected_asset: Optional[str] = None,
            reproduction_steps: Optional[str] = None,
            remediation_recommendation: Optional[str] = None,
            business_impact: Optional[str] = None,
            control_id: Optional[int] = None
        ) -> Dict[str, Any]:
            """
            Create a comprehensive security finding or compliance gap.
            
            Args:
                assessment_id: Assessment ID this finding belongs to
                project_id: Project ID this finding belongs to
                title: Clear, concise finding title
                description: Detailed description of the finding
                severity: Severity level (critical, high, medium, low, info)
                cvss_score: CVSS score (0.0-10.0)
                category: OWASP category
                affected_asset: Affected system/asset name
                reproduction_steps: Step-by-step reproduction instructions
                remediation_recommendation: Recommended remediation actions
                business_impact: Business impact analysis
                control_id: Related control ID (optional)
            
            Returns:
                Created finding with finding_id
            """
            return await self._execute_tool_via_orchestrator(
                "create_finding",
                {
                    "assessment_id": assessment_id,
                    "project_id": project_id,
                    "title": title,
                    "description": description,
                    "severity": severity,
                    "cvss_score": cvss_score,
                    "category": category,
                    "affected_asset": affected_asset,
                    "reproduction_steps": reproduction_steps,
                    "remediation_recommendation": remediation_recommendation,
                    "business_impact": business_impact,
                    "control_id": control_id
                }
            )
        
        tools.append(create_finding)
        
        return tools
    
    async def _execute_tool_via_orchestrator(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool by delegating to existing AI Task Orchestrator.
        This maintains backward compatibility with existing tool handlers.
        """
        try:
            # The orchestrator handles task creation and execution
            result = await ai_task_orchestrator.execute_tool(
                tool_name=tool_name,
                arguments=arguments
            )
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    def _get_tools_for_role(self, user_role: str) -> List[Tool]:
        """Filter tools based on user role (RBAC enforcement)"""
        
        AUDITOR_ONLY_TOOLS = ['create_project', 'create_controls']
        ANALYST_ONLY_TOOLS = [
            'upload_evidence',
            'submit_for_review',
            'request_evidence_upload',
            'submit_evidence_for_review'
        ]
        EVIDENCE_QUERY_TOOLS = [
            'analyze_evidence',
            'analyze_evidence_for_control',
            'suggest_related_controls',
            'get_evidence_by_control',
            'get_recent_evidence',
            'resolve_control_to_evidence'
        ]
        ASSESSMENT_FINDING_TOOLS = ['create_assessment', 'create_finding']
        COMMON_TOOLS = [
            'mcp_analyze_compliance',
            'generate_report',
            'search_documents',
            'list_projects',
            'fetch_evidence'
        ]
        
        user_role_lower = user_role.lower()
        
        if user_role_lower == 'super_admin':
            return self.all_tools
        
        elif user_role_lower == 'auditor':
            allowed = AUDITOR_ONLY_TOOLS + ASSESSMENT_FINDING_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
            return [t for t in self.all_tools if t.name in allowed]
        
        elif user_role_lower == 'analyst':
            allowed = ANALYST_ONLY_TOOLS + ASSESSMENT_FINDING_TOOLS + EVIDENCE_QUERY_TOOLS + COMMON_TOOLS
            return [t for t in self.all_tools if t.name in allowed]
        
        else:
            # Viewer or unknown: No tool access
            return []
    
    def _build_system_prompt(self, user_role: str, agency_name: str, username: str) -> str:
        """Build role-specific system prompt"""
        
        base_prompt = """You are an AI compliance assistant for Singapore IM8 compliance tasks.

Available Controls: 1 (Test), 3 (Network segmentation), 4 (Data encryption), 5 (MFA for privileged accounts)

EVIDENCE BUSINESS RULES:
- Evidence is PERMANENTLY BOUND to one Control (immutable binding)
- Evidence CANNOT be reassigned to a different Control or Project
- Analyst can submit MULTIPLE evidences per Control until audit closes
- If user asks to "move" or "reassign" evidence: Explain it's not allowed

CORE RULES:
1. Ask ONE question at a time
2. Only ask if information is missing AND cannot be obtained from context or tools
3. Stay focused on user's current request
4. Be concise - use minimum words needed
5. Execute tools immediately when all required fields are collected
"""
        
        role_prompts = {
            "auditor": """

AUDITOR ACTIONS:
- Create projects and controls
- Create assessments and findings
- Review evidence submissions
- Generate compliance reports
- Query evidence relationships
""",
            "analyst": """

ANALYST ACTIONS:
- Upload evidence for controls
- Analyze evidence quality
- Submit evidence for review
- Create assessments and findings
- View compliance status
""",
            "viewer": """

VIEWER ACTIONS:
- View compliance status
- View reports
- No tool access (read-only)
"""
        }
        
        user_context = f"""

CURRENT USER CONTEXT:
- Username: {username}
- Role: {user_role.upper()}
- Agency: {agency_name}

You are currently assisting {username} from {agency_name}.
"""
        
        return base_prompt + role_prompts.get(user_role.lower(), "") + user_context
    
    async def chat(
        self,
        message: str,
        session_id: str,
        db: Session,
        current_user: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message using Agent Framework
        
        Args:
            message: User's message
            session_id: Conversation session ID (used as thread_id)
            db: Database session
            current_user: Current user context
            file_path: Optional uploaded file path
        
        Returns:
            Response dictionary with answer and tool execution results
        """
        try:
            # Get user's agency name
            from api.src.models import Agency
            agency_name = "Unknown Agency"
            if current_user.get("agency_id"):
                agency = db.query(Agency).filter(Agency.id == current_user["agency_id"]).first()
                if agency:
                    agency_name = agency.name
            
            # Get role-specific tools
            user_role = current_user.get("role", "viewer")
            filtered_tools = self._get_tools_for_role(user_role)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(
                user_role=user_role,
                agency_name=agency_name,
                username=current_user.get("username", "Unknown")
            )
            
            # Create agent with role-specific tools
            agent = Agent(
                name="ComplianceAssistant",
                model=self.client,
                tools=filtered_tools,
                system_message=system_prompt,
                checkpointer=self.checkpointer
            )
            
            # Prepare user message
            user_content = message
            if file_path:
                user_content += f"\n[File uploaded: {os.path.basename(file_path)}]"
            
            # Run agent with conversation state
            response = await agent.run(
                messages=[{"role": "user", "content": user_content}],
                thread_id=session_id,  # Maps to conversation session
                config={
                    "user_id": current_user.get("id"),
                    "agency_id": current_user.get("agency_id"),
                    "file_path": file_path
                }
            )
            
            # Extract tool calls from response
            tool_calls = []
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_calls.append({
                        "tool": tool_call.name,
                        "arguments": tool_call.arguments,
                        "result": tool_call.result
                    })
            
            logger.info(f"Agent Framework processed message for session {session_id}")
            
            return {
                "answer": response.content,
                "tool_calls": tool_calls,
                "session_id": session_id,
                "provider": "agent_framework"
            }
            
        except Exception as e:
            logger.error(f"Agent Framework chat error: {str(e)}", exc_info=True)
            raise


# Global instance
agent_framework_assistant = AgentFrameworkAssistant()
