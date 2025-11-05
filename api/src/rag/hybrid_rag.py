"""Hybrid RAG system combining vector and graph search"""

from typing import List, Dict, Any, Optional
import asyncio
from .vector_search import vector_store
from .knowledge_graph import knowledge_graph
from .llm_service import llm_service
from api.src.config import settings


class HybridRAG:
    """Hybrid RAG system combining vector search and knowledge graph"""
    
    def __init__(self):
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.llm_service = llm_service
    
    async def search(self, query: str, search_type: str = "hybrid", top_k: int = 5) -> Dict[str, Any]:
        """Perform hybrid search combining vector and graph approaches"""
        
        if search_type == "vector":
            results = await self._vector_search(query, top_k)
        elif search_type == "graph":
            results = await self._graph_search(query, top_k)
        else:  # hybrid
            results = await self._hybrid_search(query, top_k)
        
        return {
            "results": results,
            "search_type": search_type,
            "query": query
        }
    
    async def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform vector-based semantic search"""
        return await self.vector_store.search(query, top_k)
    
    async def _graph_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform graph-based concept search"""
        return self.knowledge_graph.search(query, top_k)
    
    async def _hybrid_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform hybrid search combining both approaches"""
        
        # Get results from both methods
        vector_results = await self._vector_search(query, top_k)
        graph_results = await self._graph_search(query, top_k)
        
        # Combine and rank results
        all_results = []
        
        # Add vector results with weight
        for result in vector_results:
            result_copy = result.copy()
            result_copy["hybrid_score"] = result["similarity_score"] * 0.6  # Vector weight
            result_copy["search_type"] = "hybrid_vector"
            all_results.append(result_copy)
        
        # Add graph results with weight
        for result in graph_results:
            result_copy = result.copy()
            result_copy["hybrid_score"] = result["similarity_score"] * 0.4  # Graph weight
            result_copy["search_type"] = "hybrid_graph"
            all_results.append(result_copy)
        
        # Remove duplicates and sort by hybrid score
        seen_titles = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x["hybrid_score"], reverse=True):
            if result["title"] not in seen_titles:
                seen_titles.add(result["title"])
                unique_results.append(result)
        
        return unique_results[:top_k]
    
    async def generate_answer(self, query: str, search_results: List[Dict[str, Any]], search_type: str = "hybrid") -> str:
        """Generate an AI-powered answer based on search results"""
        
        if not search_results:
            return "I couldn't find relevant information to answer your question. Please try rephrasing or ask about specific compliance topics like controls, frameworks, or audit procedures."
        
        # Prepare context from search results
        context_parts = []
        for i, result in enumerate(search_results[:3], 1):  # Use top 3 results
            context_parts.append(f"{i}. {result['title']}: {result['content']}")
        
        context = "\n".join(context_parts)
        
        # Create messages for LLM
        system_prompt = """You are an expert compliance and cybersecurity assistant. Use the provided context to answer questions about security controls, compliance frameworks, audit procedures, and best practices. 

Guidelines:
- Provide specific, actionable advice
- Reference relevant frameworks (ISO 27001, NIST, SOC 2, etc.)
- Include implementation recommendations
- Mention compliance requirements when applicable
- If the context doesn't fully answer the question, acknowledge limitations and suggest related topics"""
        
        user_prompt = f"""Context from knowledge base:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. Include specific recommendations and reference relevant compliance frameworks where applicable."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Use the multi-provider LLM service
        try:
            return await self.llm_service.generate_completion(messages, max_tokens=500)
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._generate_mock_answer(query, search_results, search_type)
    
    def _generate_mock_answer(self, query: str, search_results: List[Dict[str, Any]], search_type: str) -> str:
        """Generate a structured answer from search results without OpenAI"""
        
        if not search_results:
            return "No relevant information found for your query."
        
        # Extract key information from results
        top_result = search_results[0]
        framework = top_result.get('framework', 'compliance framework')
        
        answer_parts = []
        
        # Intro
        answer_parts.append(f"Based on {search_type} search of our compliance knowledge base:")
        answer_parts.append("")
        
        # Main finding
        answer_parts.append(f"**{top_result['title']}** ({framework})")
        answer_parts.append(top_result['content'])
        answer_parts.append("")
        
        # Additional findings
        if len(search_results) > 1:
            answer_parts.append("**Related considerations:**")
            for result in search_results[1:3]:  # Next 2 results
                answer_parts.append(f"• {result['title']}: {result['content'][:100]}...")
            answer_parts.append("")
        
        # Implementation guidance
        if 'implement' in query.lower() or 'how' in query.lower():
            answer_parts.append("**Implementation Steps:**")
            answer_parts.append("1. Review organizational requirements and policies")
            answer_parts.append("2. Assess current controls and identify gaps")
            answer_parts.append("3. Develop implementation plan with timelines")
            answer_parts.append("4. Implement controls with proper documentation")
            answer_parts.append("5. Monitor and review effectiveness regularly")
            answer_parts.append("")
        
        # Compliance note
        answer_parts.append("**Compliance Note:** Ensure implementation aligns with your specific regulatory requirements and organizational policies. Consider consulting with your compliance team for detailed guidance.")
        
        return "\n".join(answer_parts)
    
    async def ask(self, query: str, search_type: str = "hybrid") -> Dict[str, Any]:
        """Complete RAG workflow: search + generate answer"""
        
        # Perform search
        search_response = await self.search(query, search_type)
        results = search_response["results"]
        
        # Generate AI answer
        answer = await self.generate_answer(query, results, search_type)
        
        return {
            "query": query,
            "answer": answer,
            "search_type": search_type,
            "sources": results,
            "source_count": len(results)
        }
    
    def add_document(self, document: Dict[str, Any]):
        """Add a document to the knowledge base"""
        self.vector_store.add_document(document)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider"""
        return self.llm_service.get_provider_info()


# Global hybrid RAG instance
hybrid_rag = HybridRAG()