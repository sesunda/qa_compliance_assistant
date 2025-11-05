"""Graph-based knowledge search for compliance relationships"""

from typing import List, Dict, Any, Set, Optional
import networkx as nx
from collections import defaultdict
import json


class ComplianceKnowledgeGraph:
    """Knowledge graph for compliance frameworks and relationships"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_compliance_graph()
    
    def _build_compliance_graph(self):
        """Build the compliance knowledge graph"""
        
        # Add nodes for different compliance concepts
        compliance_nodes = [
            # Frameworks
            {"id": "ISO27001", "type": "framework", "name": "ISO 27001", "description": "Information Security Management System"},
            {"id": "NIST_CSF", "type": "framework", "name": "NIST Cybersecurity Framework", "description": "Framework for improving critical infrastructure cybersecurity"},
            {"id": "SOC2", "type": "framework", "name": "SOC 2", "description": "Service Organization Control 2"},
            
            # Domains
            {"id": "ACCESS_CONTROL", "type": "domain", "name": "Access Control", "description": "Managing user access to systems and data"},
            {"id": "ASSET_MGMT", "type": "domain", "name": "Asset Management", "description": "Identification and management of organizational assets"},
            {"id": "INCIDENT_RESPONSE", "type": "domain", "name": "Incident Response", "description": "Procedures for handling security incidents"},
            {"id": "RISK_MGMT", "type": "domain", "name": "Risk Management", "description": "Identification and treatment of risks"},
            {"id": "CRYPTO", "type": "domain", "name": "Cryptography", "description": "Use of cryptographic controls"},
            
            # Controls
            {"id": "IAM", "type": "control", "name": "Identity and Access Management", "description": "Systems for managing user identities and access"},
            {"id": "ENCRYPTION", "type": "control", "name": "Encryption", "description": "Cryptographic protection of data"},
            {"id": "MONITORING", "type": "control", "name": "Security Monitoring", "description": "Continuous monitoring of security events"},
            {"id": "BACKUP", "type": "control", "name": "Data Backup", "description": "Regular backup of critical data"},
            {"id": "PATCH_MGMT", "type": "control", "name": "Patch Management", "description": "Regular updating of systems and software"},
            
            # Processes
            {"id": "AUDIT", "type": "process", "name": "Security Audit", "description": "Regular assessment of security controls"},
            {"id": "VULNERABILITY_SCAN", "type": "process", "name": "Vulnerability Scanning", "description": "Regular scanning for security vulnerabilities"},
            {"id": "PENETRATION_TEST", "type": "process", "name": "Penetration Testing", "description": "Simulated attacks to test security"},
            {"id": "RISK_ASSESSMENT", "type": "process", "name": "Risk Assessment", "description": "Systematic evaluation of risks"},
            
            # Evidence types
            {"id": "POLICY_DOC", "type": "evidence", "name": "Policy Documentation", "description": "Written security policies and procedures"},
            {"id": "SCAN_REPORT", "type": "evidence", "name": "Scan Reports", "description": "Vulnerability and compliance scan results"},
            {"id": "AUDIT_REPORT", "type": "evidence", "name": "Audit Reports", "description": "Internal and external audit findings"},
            {"id": "TRAINING_RECORD", "type": "evidence", "name": "Training Records", "description": "Security awareness training documentation"},
        ]
        
        # Add nodes to graph
        for node in compliance_nodes:
            self.graph.add_node(node["id"], **node)
        
        # Add relationships
        relationships = [
            # Framework to domain relationships
            ("ISO27001", "ACCESS_CONTROL", "includes"),
            ("ISO27001", "ASSET_MGMT", "includes"),
            ("ISO27001", "INCIDENT_RESPONSE", "includes"),
            ("ISO27001", "RISK_MGMT", "includes"),
            ("ISO27001", "CRYPTO", "includes"),
            
            ("NIST_CSF", "ACCESS_CONTROL", "includes"),
            ("NIST_CSF", "ASSET_MGMT", "includes"),
            ("NIST_CSF", "INCIDENT_RESPONSE", "includes"),
            ("NIST_CSF", "RISK_MGMT", "includes"),
            
            # Domain to control relationships
            ("ACCESS_CONTROL", "IAM", "implements"),
            ("CRYPTO", "ENCRYPTION", "implements"),
            ("ASSET_MGMT", "MONITORING", "implements"),
            ("ASSET_MGMT", "BACKUP", "implements"),
            ("RISK_MGMT", "PATCH_MGMT", "implements"),
            
            # Control to process relationships
            ("IAM", "AUDIT", "requires"),
            ("ENCRYPTION", "AUDIT", "requires"),
            ("MONITORING", "VULNERABILITY_SCAN", "enables"),
            ("BACKUP", "AUDIT", "requires"),
            ("PATCH_MGMT", "VULNERABILITY_SCAN", "requires"),
            
            # Process to evidence relationships
            ("AUDIT", "AUDIT_REPORT", "produces"),
            ("VULNERABILITY_SCAN", "SCAN_REPORT", "produces"),
            ("PENETRATION_TEST", "SCAN_REPORT", "produces"),
            ("RISK_ASSESSMENT", "AUDIT_REPORT", "produces"),
            
            # Additional evidence relationships
            ("ACCESS_CONTROL", "POLICY_DOC", "requires"),
            ("INCIDENT_RESPONSE", "POLICY_DOC", "requires"),
            ("IAM", "TRAINING_RECORD", "requires"),
            
            # Cross-framework relationships
            ("ISO27001", "NIST_CSF", "aligns_with"),
            ("SOC2", "ISO27001", "overlaps_with"),
        ]
        
        # Add relationships to graph
        for source, target, relationship in relationships:
            self.graph.add_edge(source, target, relationship=relationship)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge graph for relevant concepts"""
        
        query_lower = query.lower()
        results = []
        
        # Search nodes by name and description
        for node_id, data in self.graph.nodes(data=True):
            score = 0
            
            # Check name match
            if query_lower in data.get("name", "").lower():
                score += 2
            
            # Check description match
            if query_lower in data.get("description", "").lower():
                score += 1
            
            # Check for keyword matches
            keywords = ["control", "policy", "audit", "risk", "security", "access", "management", "assessment"]
            for keyword in keywords:
                if keyword in query_lower and keyword in data.get("description", "").lower():
                    score += 0.5
            
            if score > 0:
                result = {
                    "id": node_id,
                    "title": data.get("name", ""),
                    "content": data.get("description", ""),
                    "type": data.get("type", ""),
                    "similarity_score": min(score / 3.0, 1.0),  # Normalize to 0-1
                    "search_type": "graph",
                    "relationships": self._get_node_relationships(node_id)
                }
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
    
    def _get_node_relationships(self, node_id: str) -> List[Dict[str, str]]:
        """Get relationships for a node"""
        relationships = []
        
        # Outgoing relationships
        for target in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, target)
            target_data = self.graph.nodes[target]
            relationships.append({
                "type": "outgoing",
                "relationship": edge_data.get("relationship", ""),
                "target": target,
                "target_name": target_data.get("name", ""),
                "target_type": target_data.get("type", "")
            })
        
        # Incoming relationships
        for source in self.graph.predecessors(node_id):
            edge_data = self.graph.get_edge_data(source, node_id)
            source_data = self.graph.nodes[source]
            relationships.append({
                "type": "incoming",
                "relationship": edge_data.get("relationship", ""),
                "source": source,
                "source_name": source_data.get("name", ""),
                "source_type": source_data.get("type", "")
            })
        
        return relationships
    
    def get_related_concepts(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Get concepts related to a specific node"""
        
        if node_id not in self.graph:
            return []
        
        related = []
        visited = set()
        
        def traverse(current_id, depth):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Add direct neighbors
            for neighbor in list(self.graph.successors(current_id)) + list(self.graph.predecessors(current_id)):
                if neighbor not in visited:
                    neighbor_data = self.graph.nodes[neighbor]
                    related.append({
                        "id": neighbor,
                        "title": neighbor_data.get("name", ""),
                        "content": neighbor_data.get("description", ""),
                        "type": neighbor_data.get("type", ""),
                        "depth": depth + 1,
                        "search_type": "graph_related"
                    })
                    
                    if depth < max_depth:
                        traverse(neighbor, depth + 1)
        
        traverse(node_id, 0)
        return related
    
    def find_paths(self, source: str, target: str) -> List[List[str]]:
        """Find paths between two concepts"""
        
        if source not in self.graph or target not in self.graph:
            return []
        
        try:
            # Find shortest paths (up to 5)
            paths = list(nx.all_shortest_paths(self.graph, source, target))
            return paths[:5]  # Limit to 5 paths
        except nx.NetworkXNoPath:
            return []


# Global knowledge graph instance
knowledge_graph = ComplianceKnowledgeGraph()