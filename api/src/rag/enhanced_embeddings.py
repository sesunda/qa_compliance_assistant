"""Enhanced embeddings with relationship context for Graph RAG capabilities"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import hashlib
import json
import os
from functools import lru_cache

class EnhancedEmbeddingService:
    """Enhanced embedding service with relationship context for agentic reasoning"""
    
    def __init__(self):
        self.model = None
        self.model_name = "all-MiniLM-L6-v2"  # 384 dimensions, fast, good quality
        self.embedding_dim = 384
        
        # Singapore IM8 specific relationships
        self.im8_relationships = {
            "frameworks": {
                "IM8": ["Information Management", "Singapore Government", "Data Governance"],
                "ISO27001": ["Information Security", "International Standard"],
                "NIST": ["Cybersecurity Framework", "Risk Management"],
                "SOX": ["Financial Controls", "Audit Compliance"]
            },
            "control_dependencies": {
                # IM8 Agent controls and their dependencies
                "IM8.AC.01": ["identity_management", "access_reviews", "privileged_access"],
                "IM8.AC.02": ["authentication", "multi_factor", "identity_verification"],
                "IM8.DG.01": ["data_classification", "data_lifecycle", "data_retention"],
                "IM8.DG.02": ["data_protection", "encryption", "access_controls"],
                "IM8.RM.01": ["risk_assessment", "risk_monitoring", "risk_treatment"],
                "IM8.RM.02": ["incident_response", "business_continuity", "disaster_recovery"]
            },
            "singapore_context": {
                "government_agencies": ["Whole-of-Government", "Smart Nation", "Digital Government"],
                "regulations": ["PDPA", "Cybersecurity Act", "Government Instruction Manual"],
                "sectors": ["Public Sector", "Critical Information Infrastructure", "Smart Systems"]
            },
            "control_mappings": {
                # Map common concepts to IM8 controls
                "access_control": ["IM8.AC.01", "IM8.AC.02", "IM8.AC.03"],
                "data_governance": ["IM8.DG.01", "IM8.DG.02", "IM8.DG.03"],
                "risk_management": ["IM8.RM.01", "IM8.RM.02", "IM8.RM.03"],
                "incident_management": ["IM8.IM.01", "IM8.IM.02", "IM8.IM.03"]
            }
        }
        
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            print("📥 Loading sentence-transformers model...")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Sentence transformers loaded: {self.model_name}")
        except Exception as e:
            print(f"❌ Failed to load sentence transformers: {e}")
            print("🔄 Falling back to mock embeddings")
            self.model = None
    
    @lru_cache(maxsize=1000)
    def get_enhanced_embedding(self, text: str, context_type: str = "general") -> List[float]:
        """Get embedding with relationship context for enhanced semantic understanding"""
        
        # Enhance text with relationship context
        enhanced_text = self._add_relationship_context(text, context_type)
        
        if self.model is not None:
            try:
                # Use real sentence transformers
                embedding = self.model.encode(enhanced_text, convert_to_tensor=False)
                return embedding.tolist()
            except Exception as e:
                print(f"❌ Sentence transformer error: {e}")
                return self._fallback_embedding(enhanced_text)
        else:
            # Fallback to deterministic embeddings
            return self._fallback_embedding(enhanced_text)
    
    def _add_relationship_context(self, text: str, context_type: str) -> str:
        """Add relationship context to text for graph-like understanding"""
        
        context_parts = []
        text_lower = text.lower()
        
        # Add framework context
        framework_context = []
        for framework, keywords in self.im8_relationships["frameworks"].items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                framework_context.append(framework)
        
        # Add Singapore-specific context
        singapore_context = []
        for category, terms in self.im8_relationships["singapore_context"].items():
            matching_terms = [term for term in terms if term.lower() in text_lower]
            if matching_terms:
                singapore_context.extend(matching_terms)
        
        # Add control mapping context
        control_context = []
        for concept, controls in self.im8_relationships["control_mappings"].items():
            if concept.replace("_", " ") in text_lower:
                control_context.extend(controls)
        
        # Build enhanced context
        if framework_context:
            context_parts.append(f"frameworks: {', '.join(framework_context)}")
        
        if singapore_context:
            context_parts.append(f"singapore_context: {', '.join(singapore_context)}")
        
        if control_context:
            context_parts.append(f"im8_controls: {', '.join(control_context[:3])}")  # Limit to top 3
        
        # Add dependency context for known controls
        dependency_context = []
        for control_id, deps in self.im8_relationships["control_dependencies"].items():
            if control_id in text or any(dep.replace("_", " ") in text_lower for dep in deps):
                dependency_context.extend(deps)
        
        if dependency_context:
            context_parts.append(f"dependencies: {', '.join(set(dependency_context[:5]))}")
        
        # Construct enhanced text
        if context_parts:
            enhanced_text = f"{text} | {' | '.join(context_parts)}"
        else:
            enhanced_text = text
        
        return enhanced_text
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Generate deterministic fallback embedding"""
        # Use text hash as seed for consistent embeddings
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        
        # Generate embedding with correct dimensions
        embedding = np.random.uniform(-1, 1, self.embedding_dim)
        
        # Normalize vector
        magnitude = np.linalg.norm(embedding)
        if magnitude > 0:
            embedding = embedding / magnitude
        
        return embedding.tolist()
    
    def get_control_relationships(self, control_id: str) -> Dict[str, List[str]]:
        """Get relationship context for a specific control"""
        relationships = {
            "dependencies": self.im8_relationships["control_dependencies"].get(control_id, []),
            "framework": "IM8" if control_id.startswith("IM8") else "Unknown",
            "singapore_context": []
        }
        
        # Add relevant Singapore context based on control type
        if "AC" in control_id:  # Access Control
            relationships["singapore_context"] = ["Government Access Management", "Privileged User Controls"]
        elif "DG" in control_id:  # Data Governance
            relationships["singapore_context"] = ["Government Data Standards", "PDPA Compliance"]
        elif "RM" in control_id:  # Risk Management
            relationships["singapore_context"] = ["Government Risk Framework", "Cybersecurity Act"]
        
        return relationships
    
    def batch_embed(self, texts: List[str], context_type: str = "general") -> List[List[float]]:
        """Batch embedding for efficiency"""
        if self.model is not None:
            try:
                # Add context to all texts
                enhanced_texts = [self._add_relationship_context(text, context_type) for text in texts]
                embeddings = self.model.encode(enhanced_texts, convert_to_tensor=False, show_progress_bar=True)
                return embeddings.tolist()
            except Exception as e:
                print(f"❌ Batch embedding error: {e}")
                return [self._fallback_embedding(self._add_relationship_context(text, context_type)) for text in texts]
        else:
            return [self._fallback_embedding(self._add_relationship_context(text, context_type)) for text in texts]

# Global instance
enhanced_embedding_service = EnhancedEmbeddingService()