"""
Interactive Learning Tests for Vector Search Concepts

Run this to understand embeddings, hybrid search, and Azure AI Search features.
Each test is self-contained and demonstrates a specific concept.
"""

import asyncio
import numpy as np
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# TEST 1: Vector Embeddings - Text to 1536D Numbers
# ============================================================================

async def test_vector_embeddings():
    """
    🎓 CONCEPT: Vector Embeddings
    
    Text is converted to high-dimensional vectors (arrays of numbers).
    Similar meanings = similar vectors (measured by cosine similarity)
    """
    print("\n" + "="*70)
    print("TEST 1: VECTOR EMBEDDINGS - Text → 1536D Numbers")
    print("="*70)
    
    from api.src.rag.llm_service import llm_service
    
    # Test sentences with different relationships
    test_cases = [
        {
            "text1": "password requirements",
            "text2": "authentication policy",
            "expected": "HIGH similarity (same concept)"
        },
        {
            "text1": "password requirements",
            "text2": "network firewall",
            "expected": "LOW similarity (different concepts)"
        },
        {
            "text1": "multi-factor authentication",
            "text2": "two-factor authentication",
            "expected": "VERY HIGH similarity (synonyms)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"   Text 1: '{test['text1']}'")
        print(f"   Text 2: '{test['text2']}'")
        print(f"   Expected: {test['expected']}")
        
        # Generate embeddings
        embedding1 = await llm_service.get_embedding(test['text1'])
        embedding2 = await llm_service.get_embedding(test['text2'])
        
        # Show embedding properties
        print(f"\n   📊 Embedding Properties:")
        print(f"      - Dimensions: {len(embedding1)} numbers")
        print(f"      - First 5 values: {embedding1[:5]}")
        print(f"      - Range: [{min(embedding1):.4f}, {max(embedding1):.4f}]")
        
        # Calculate cosine similarity
        similarity = cosine_similarity_manual(embedding1, embedding2)
        
        print(f"\n   🎯 Cosine Similarity: {similarity:.4f}")
        print(f"      - 1.0 = identical meaning")
        print(f"      - 0.8-0.9 = very similar")
        print(f"      - 0.6-0.8 = related")
        print(f"      - <0.6 = different")
        
        # Interpretation
        if similarity > 0.85:
            result = "✅ VERY SIMILAR (same concept)"
        elif similarity > 0.7:
            result = "✅ SIMILAR (related concepts)"
        else:
            result = "❌ DIFFERENT (unrelated)"
        
        print(f"\n   Result: {result}")
        print("   " + "-"*66)


def cosine_similarity_manual(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)
    
    return dot_product / (magnitude1 * magnitude2)


# ============================================================================
# TEST 2: Hybrid Search - Keyword vs Vector vs Combined
# ============================================================================

async def test_hybrid_search():
    """
    🎓 CONCEPT: Hybrid Search
    
    Combines:
    - Keyword search (BM25): Exact word matching
    - Vector search: Semantic understanding
    - Result: Better recall than either alone
    """
    print("\n" + "="*70)
    print("TEST 2: HYBRID SEARCH - Keyword + Vector = Better Recall")
    print("="*70)
    
    from api.src.rag.vector_search import vector_store
    
    # Ensure documents are indexed
    await vector_store.index_documents()
    
    query = "How to protect user credentials?"
    
    print(f"\n🔍 Query: '{query}'")
    print("\nComparing search methods:\n")
    
    # Method 1: Pure Keyword Search (simulated)
    print("📄 METHOD 1: KEYWORD SEARCH ONLY")
    print("   Logic: Find documents containing words 'protect', 'user', 'credentials'")
    keyword_matches = []
    for doc in vector_store.documents:
        text = f"{doc['title']} {doc['content']}".lower()
        if 'credential' in text or 'password' in text:
            keyword_matches.append(doc)
    
    print(f"   Results: {len(keyword_matches)} documents")
    for doc in keyword_matches[:3]:
        print(f"      - [{doc['framework']}] {doc['title']}")
    
    # Method 2: Pure Vector Search
    print("\n🧠 METHOD 2: VECTOR (SEMANTIC) SEARCH ONLY")
    print("   Logic: Find documents with similar MEANING (even if words differ)")
    vector_results = await vector_store.search(query, top_k=3)
    print(f"   Results: {len(vector_results)} documents")
    for doc in vector_results:
        print(f"      - [{doc['framework']}] {doc['title']}")
        print(f"        Similarity: {doc['similarity_score']:.4f}")
    
    # Method 3: Hybrid (what Azure AI Search does)
    print("\n⚡ METHOD 3: HYBRID SEARCH (Keyword + Vector)")
    print("   Logic: Combines both methods, scores higher if:")
    print("          - Contains matching keywords AND")
    print("          - Has similar semantic meaning")
    print("   Results: Best of both worlds")
    print("      - Finds exact matches (keyword)")
    print("      - Also finds synonyms/related concepts (vector)")
    
    print("\n💡 WHY HYBRID IS BETTER:")
    print("   ✅ Keyword finds: 'credential', 'password' (exact)")
    print("   ✅ Vector finds: 'authentication', 'access control' (meaning)")
    print("   ✅ Combined: Maximum recall, no missed documents")


# ============================================================================
# TEST 3: Feature Flags - Safe Rollout Pattern
# ============================================================================

async def test_feature_flags():
    """
    🎓 CONCEPT: Feature Flags
    
    Control features via environment variables.
    Benefits:
    - Zero downtime switching
    - Safe testing in production
    - Instant rollback if issues
    """
    print("\n" + "="*70)
    print("TEST 3: FEATURE FLAGS - Safe Rollout Pattern")
    print("="*70)
    
    from api.src.rag.vector_search import UnifiedVectorSearch, vector_store
    from api.src.config import settings
    
    print(f"\n🎚️  Current Feature Flag: AZURE_SEARCH_ENABLED = {settings.AZURE_SEARCH_ENABLED}")
    
    # Show current backend
    search = UnifiedVectorSearch()
    backend_info = search.get_backend_info()
    
    print(f"\n📊 Active Backend:")
    print(f"   Name: {backend_info['backend']}")
    print(f"   Features: {', '.join(backend_info['features'])}")
    
    if 'document_count' in backend_info:
        print(f"   Documents: {backend_info['document_count']}")
    
    # Demonstrate safe switching
    print("\n🔄 HOW FEATURE FLAGS ENABLE SAFE ROLLOUT:")
    print("\n   Step 1: Development")
    print("      AZURE_SEARCH_ENABLED=false")
    print("      → Uses in-memory (fast, stable)")
    
    print("\n   Step 2: Testing")
    print("      AZURE_SEARCH_ENABLED=true")
    print("      → Switches to Azure AI Search")
    print("      → Compare results, check performance")
    
    print("\n   Step 3: Production (Canary)")
    print("      10% of users: AZURE_SEARCH_ENABLED=true")
    print("      90% of users: AZURE_SEARCH_ENABLED=false")
    print("      → Gradual rollout, monitor metrics")
    
    print("\n   Step 4: Full Rollout or Rollback")
    print("      If success: All users → true")
    print("      If issues: All users → false (instant rollback)")
    
    print("\n   ✅ Zero Code Changes Required!")
    print("   ✅ Change environment variable only")
    print("   ✅ No redeploy needed")


# ============================================================================
# TEST 4: HNSW Algorithm - Fast Approximate Search
# ============================================================================

async def test_hnsw_algorithm():
    """
    🎓 CONCEPT: HNSW (Hierarchical Navigable Small World)
    
    Makes vector search 100x faster with 99%+ accuracy.
    Used by: Spotify, Pinterest, Microsoft, Google
    """
    print("\n" + "="*70)
    print("TEST 4: HNSW ALGORITHM - Fast Approximate Nearest Neighbor")
    print("="*70)
    
    print("\n🎯 THE PROBLEM:")
    print("   Finding nearest neighbors in high dimensions is SLOW")
    print("   - 1,000 documents × 1536 dimensions = 1.5M comparisons")
    print("   - Exact search: O(n) = linear time")
    print("   - 1M documents? Hours to search!")
    
    print("\n💡 THE SOLUTION: HNSW")
    print("   Builds a multi-layer graph structure:")
    print()
    print("   Layer 2 (top):     •─────•─────•  (long jumps)")
    print("                      │     │     │")
    print("   Layer 1:        •──•──•──•──•──•  (medium jumps)")
    print("                   │  │  │  │  │  │")
    print("   Layer 0 (base): •─•─•─•─•─•─•─•  (fine-grained)")
    print()
    print("   Search path:")
    print("   1. Start at top layer (few nodes)")
    print("   2. Jump to closest node")
    print("   3. Move down to next layer")
    print("   4. Repeat until base layer")
    print("   5. Found! (logarithmic time)")
    
    print("\n📊 PERFORMANCE COMPARISON:")
    print("   Exact Search (brute force):")
    print("      - 1,000 docs: 1,000 comparisons (~1ms)")
    print("      - 1M docs: 1,000,000 comparisons (~1 second)")
    print("      - 100M docs: 100,000,000 comparisons (~100 seconds)")
    
    print("\n   HNSW (approximate):")
    print("      - 1,000 docs: ~10 comparisons (~0.01ms)")
    print("      - 1M docs: ~20 comparisons (~0.02ms)")
    print("      - 100M docs: ~30 comparisons (~0.03ms)")
    
    print("\n   🚀 Result: 100-1000x faster!")
    print("   ✅ Accuracy: 99%+ (acceptable trade-off)")
    
    print("\n⚙️  HNSW PARAMETERS (in azure_search.py):")
    print("   - m=4: Connections per node (higher = more accurate, slower)")
    print("   - efConstruction=400: Build-time accuracy")
    print("   - efSearch=500: Query-time accuracy")
    print("   - metric=cosine: Distance calculation method")


# ============================================================================
# TEST 5: Index Schema - Document Structure
# ============================================================================

async def test_index_schema():
    """
    🎓 CONCEPT: Index Schema
    
    Defines how documents are structured and searchable.
    Like a database table schema, but for search.
    """
    print("\n" + "="*70)
    print("TEST 5: INDEX SCHEMA - Document Structure for Search")
    print("="*70)
    
    from api.src.rag.vector_search import vector_store
    
    # Show example document
    doc = vector_store.documents[0]
    
    print("\n📄 EXAMPLE COMPLIANCE DOCUMENT:")
    print(f"   ID: {doc['id']}")
    print(f"   Title: {doc['title']}")
    print(f"   Framework: {doc['framework']}")
    print(f"   Category: {doc['category']}")
    print(f"   Content: {doc['content'][:100]}...")
    
    print("\n🏗️  INDEX SCHEMA DESIGN:")
    print("\n   1. SIMPLE FIELDS (filterable, sortable):")
    print("      - id: String (key=True)")
    print("        → Unique identifier")
    print("      - framework: String (filterable=True)")
    print("        → Filter: 'framework eq \"ISO 27001\"'")
    print("      - category: String (filterable=True, facetable=True)")
    print("        → Filter + count by category")
    
    print("\n   2. SEARCHABLE FIELDS (full-text search):")
    print("      - title: String (searchable=True)")
    print("        → Keyword matching on title")
    print("      - content: String (searchable=True)")
    print("        → Main text search target")
    
    print("\n   3. VECTOR FIELD (semantic search):")
    print("      - content_vector: Collection(Single)")
    print("        → 1536-dimensional embedding")
    print("        → Enables semantic similarity search")
    
    print("\n💡 WHY THIS STRUCTURE?")
    print("   ✅ Enables: 'Find ISO 27001 access control requirements'")
    print("      1. Filter: framework = 'ISO 27001' (exact)")
    print("      2. Filter: category = 'access_control' (exact)")
    print("      3. Search: 'requirements' (keyword + vector)")
    
    print("\n📊 FIELD TYPE COMPARISON:")
    print("   ┌─────────────────┬──────────┬────────────┬─────────┐")
    print("   │ Field Type      │ Filterable│ Searchable│ Sortable│")
    print("   ├─────────────────┼──────────┼────────────┼─────────┤")
    print("   │ SimpleField     │    ✅     │     ❌     │   ✅    │")
    print("   │ SearchableField │    ❌     │     ✅     │   ❌    │")
    print("   │ VectorField     │    ❌     │     ✅*    │   ❌    │")
    print("   └─────────────────┴──────────┴────────────┴─────────┘")
    print("   * Searchable via vector similarity, not keywords")


# ============================================================================
# TEST 6: End-to-End Query Example
# ============================================================================

async def test_end_to_end_query():
    """
    🎓 CONCEPT: Complete Search Pipeline
    
    Demonstrates how all concepts work together in a real query.
    """
    print("\n" + "="*70)
    print("TEST 6: END-TO-END QUERY - All Concepts Together")
    print("="*70)
    
    from api.src.rag.vector_search import vector_store
    
    query = "What are the password security requirements?"
    
    print(f"\n🔍 User Query: '{query}'")
    print("\n📋 SEARCH PIPELINE:")
    
    print("\n   Step 1: EMBEDDING GENERATION")
    print("      Input: 'What are the password security requirements?'")
    from api.src.rag.llm_service import llm_service
    query_embedding = await llm_service.get_embedding(query)
    print(f"      Output: 1536D vector [{query_embedding[:3]}...]")
    
    print("\n   Step 2: VECTOR SIMILARITY SEARCH")
    print("      - Compare query vector with all document vectors")
    print("      - Calculate cosine similarity for each")
    print("      - Rank by similarity score")
    
    print("\n   Step 3: RETRIEVE TOP RESULTS")
    results = await vector_store.search(query, top_k=3)
    print(f"      Found {len(results)} relevant documents:")
    
    for i, doc in enumerate(results, 1):
        print(f"\n      Result {i}:")
        print(f"         Framework: {doc['framework']}")
        print(f"         Title: {doc['title']}")
        print(f"         Score: {doc['similarity_score']:.4f}")
        print(f"         Match: ", end="")
        if doc['similarity_score'] > 0.85:
            print("🟢 HIGHLY RELEVANT")
        elif doc['similarity_score'] > 0.7:
            print("🟡 RELEVANT")
        else:
            print("🔴 SOMEWHAT RELEVANT")
    
    print("\n   Step 4: RETURN TO USER")
    print("      - Format results as JSON")
    print("      - Include relevance scores")
    print("      - User sees most relevant compliance controls")
    
    print("\n✅ COMPLETE PIPELINE:")
    print("   Query → Embedding → Vector Search → Ranking → Results")


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_all_tests():
    """Run all interactive learning tests"""
    
    print("\n" + "🎓 "*20)
    print("INTERACTIVE LEARNING TESTS - VECTOR SEARCH CONCEPTS")
    print("🎓 "*20)
    
    tests = [
        ("Vector Embeddings", test_vector_embeddings),
        ("Hybrid Search", test_hybrid_search),
        ("Feature Flags", test_feature_flags),
        ("HNSW Algorithm", test_hnsw_algorithm),
        ("Index Schema", test_index_schema),
        ("End-to-End Query", test_end_to_end_query),
    ]
    
    for name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*70)
    print("\n📚 KEY TAKEAWAYS:")
    print("   1. Embeddings convert text to vectors for similarity")
    print("   2. Hybrid search combines keyword + semantic")
    print("   3. Feature flags enable safe rollout")
    print("   4. HNSW makes search 100x faster")
    print("   5. Index schema defines searchable structure")
    print("   6. All concepts work together in the pipeline")
    
    print("\n💡 NEXT STEPS:")
    print("   - Enable Azure AI Search: AZURE_SEARCH_ENABLED=true")
    print("   - Compare search quality with in-memory")
    print("   - Test hybrid search with real queries")
    print("   - Scale to hundreds of documents")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
