# RAG (Retrieval-Augmented Generation) Feature Explanation

## Overview

The QA Compliance Assistant implements a sophisticated **Hybrid RAG system** that combines multiple AI techniques to provide intelligent, context-aware responses to compliance questions and document analysis.

## Architecture Components

### 1. **Hybrid RAG System** (`api/src/rag/hybrid_rag.py`)

The core of the RAG feature combines three search strategies:

#### **Vector Search**
- Uses semantic embeddings to find similar content
- Converts text into 1536-dimensional vectors
- Calculates cosine similarity between query and documents
- Excellent for finding conceptually similar information

#### **Graph Search**
- Uses a knowledge graph to find related concepts
- Represents compliance frameworks, controls, and relationships as nodes and edges
- Performs graph traversal to discover connections
- Ideal for understanding relationships between compliance elements

#### **Hybrid Search** (Default)
- Combines both vector and graph search results
- Weighted scoring: 60% vector similarity + 40% graph relevance
- Removes duplicates and ranks by combined score
- Provides most comprehensive results

### 2. **Vector Store** (`api/src/rag/vector_search.py`)

**Pre-loaded Knowledge Base includes:**

- **ISO 27001 Controls**:
  - Information Security Policy (A.5.1.1)
  - Inventory of Assets (A.8.1.1)
  - Access Control Policy (A.9.1.1)
  - Documented Operating Procedures (A.12.1.1)

- **NIST Cybersecurity Framework**:
  - Physical device inventory (ID.AM-1)
  - Identity and credential management (PR.AC-1)
  - Network monitoring (DE.CM-1)

- **Compliance Best Practices**:
  - Risk Assessment Methodology
  - Evidence Collection and Management
  - Incident Response Planning

**How Vector Search Works:**

1. **Document Indexing**: Each document (title + content) is converted to an embedding vector
2. **Query Embedding**: User query is converted to the same vector space
3. **Similarity Calculation**: Cosine similarity computed between query and all documents
4. **Ranking**: Top K documents with similarity > 0.7 threshold are returned
5. **Caching**: Embeddings are cached to improve performance

### 3. **Knowledge Graph** (`api/src/rag/knowledge_graph.py`)

**Graph Structure:**

```
Frameworks (ISO 27001, NIST CSF, SOC 2)
    ↓ includes
Domains (Access Control, Asset Management, Risk Management)
    ↓ implements
Controls (IAM, Encryption, Monitoring, Backup, Patch Management)
    ↓ requires
Processes (Audit, Vulnerability Scanning, Penetration Testing)
    ↓ produces
Evidence (Policy Docs, Scan Reports, Audit Reports, Training Records)
```

**Graph Search Features:**

- **BFS (Breadth-First Search)**: Finds all related nodes within a certain depth
- **Relationship Traversal**: Discovers connections between concepts
- **Similarity Scoring**: Ranks results based on graph distance and relevance
- **Multi-hop Reasoning**: Can trace paths like: "ISO 27001 → Access Control → IAM → Audit → Audit Report"

### 4. **Multi-Provider LLM Service** (`api/src/rag/llm_service.py`)

Supports multiple AI providers:

- **Azure OpenAI**: GPT-4 for production use
- **GitHub Models**: GPT-4o (free tier) for development
- **Groq**: Llama 3.1 70B for fast inference
- **Ollama**: Local models for offline operation

**LLM Capabilities:**

- Generate embeddings (text → vectors)
- Generate completions (context + query → answer)
- Summarize documents
- Extract key information

### 5. **Agentic Assistant Integration** (`api/src/services/agentic_assistant.py`)

The RAG system is integrated with the Agentic Chat for advanced capabilities:

**Tool Calling:**
- Upload evidence documents
- Create security findings
- Generate compliance reports
- Analyze evidence relationships
- Query control mappings

**Conversation Memory:**
- Multi-turn conversations with session persistence
- Context carried across multiple interactions
- Database storage with JSON and normalized schemas

## User Workflow

### 1. **Document Upload with RAG Analysis**

**Frontend** (`frontend/src/pages/RAGPage.tsx`):
```typescript
// User uploads a PDF/DOCX document
const formData = new FormData()
formData.append('file', selectedFile)
formData.append('query', 'Analyze this evidence document')
formData.append('search_type', 'hybrid')

// Send to RAG endpoint
const response = await api.post('/rag/ask-with-file', formData)
```

**Backend Processing** (`api/src/routers/rag.py`):
```python
@router.post("/ask-with-file")
async def ask_with_file(file, query, search_type):
    # 1. Save uploaded file to storage
    # 2. Create/restore conversation session
    # 3. Use agentic assistant with file context
    # 4. Perform hybrid RAG search
    # 5. Generate AI-powered answer
    # 6. Return results with sources
```

### 2. **Question Answering Flow**

**Step 1: User asks question**
```
User: "What are the requirements for access control in ISO 27001?"
```

**Step 2: Hybrid search executes**
- Vector search finds similar documents about access control
- Graph search finds related concepts (IAM, policies, audit requirements)
- Results combined with weighted scoring

**Step 3: Context preparation**
```python
# Top 3 results used as context
context = """
1. Access Control Policy (A.9.1.1): An access control policy should be...
2. Identity and Access Management: Systems for managing user identities...
3. Security Audit: Regular assessment of security controls...
"""
```

**Step 4: LLM generates answer**
```python
system_prompt = "You are an expert compliance assistant..."
user_prompt = f"Context: {context}\n\nQuestion: {query}"

# LLM generates comprehensive answer referencing the context
answer = await llm_service.generate_completion(messages)
```

**Step 5: Response returned**
```json
{
  "query": "What are the requirements for access control in ISO 27001?",
  "answer": "Based on ISO 27001 standard...",
  "search_type": "hybrid",
  "sources": [
    {
      "id": "A.9.1.1",
      "title": "Access Control Policy",
      "content": "...",
      "similarity_score": 0.92,
      "framework": "ISO 27001"
    }
  ],
  "source_count": 3
}
```

### 3. **Session Persistence**

**Conversation Memory:**
- Each chat session gets a unique `session_id`
- Stored in localStorage for session restoration
- Messages saved to database in real-time
- Full conversation history restored on page reload

**Database Schema:**
```sql
-- JSON-based storage (primary)
conversation_sessions (
  session_id UUID PRIMARY KEY,
  user_id INTEGER,
  title TEXT,
  messages JSONB,  -- Array of {role, content, timestamp}
  created_at TIMESTAMP,
  last_activity TIMESTAMP
)

-- Normalized storage (analytics)
conversation_messages (
  id SERIAL PRIMARY KEY,
  session_id UUID,
  role TEXT,
  content TEXT,
  timestamp TIMESTAMP,
  tool_calls JSONB
)
```

## Advanced Features

### 1. **Multi-Modal Input**
- Text queries
- File uploads (PDF, DOCX, TXT)
- Voice input (speech-to-text with Whisper)
- Combined text + document analysis

### 2. **Task Orchestration**
The RAG system can trigger automated tasks:

```python
# User: "Upload this evidence for Control 3"
# RAG detects intent and executes:
await agentic_assistant.upload_evidence_tool(
    control_id=3,
    file_path="/storage/evidence/document.pdf",
    title="Evidence document",
    evidence_type="policy"
)
```

### 3. **Search Type Selection**

**Vector Search** - Best for:
- Conceptual similarity
- "What controls relate to encryption?"
- Finding similar policies

**Graph Search** - Best for:
- Relationship discovery
- "What evidence is needed for ISO 27001 access control?"
- Framework mappings

**Hybrid Search** - Best for:
- General questions
- Comprehensive answers
- Balanced relevance

### 4. **Intelligent Response Generation**

**System Prompt Guidelines:**
```
- Provide specific, actionable advice
- Reference relevant frameworks (ISO 27001, NIST, SOC 2)
- Include implementation recommendations
- Mention compliance requirements
- Acknowledge limitations when context insufficient
```

**Structured Fallback:**
If LLM service fails, generates structured response:
```
Based on hybrid search:

**Access Control Policy** (ISO 27001)
[Main content]

**Related considerations:**
• Identity and Access Management: Systems for managing...
• Security Audit: Regular assessment of security controls...

**Implementation Steps:**
1. Review organizational requirements
2. Assess current controls
3. Develop implementation plan
4. Implement with documentation
5. Monitor and review regularly

**Compliance Note:** Ensure alignment with regulatory requirements...
```

## Technical Implementation Details

### Embedding Generation

**Using Azure OpenAI:**
```python
async def get_embedding(self, text: str) -> List[float]:
    response = await openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding  # 1536 dimensions
```

**Mock Embeddings (for demo):**
```python
def _generate_mock_embedding(self, text: str) -> List[float]:
    # Hash text for consistent seed
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    # Generate normalized 1536-dimensional vector
    embedding = [random.uniform(-1, 1) for _ in range(1536)]
    magnitude = sum(x*x for x in embedding) ** 0.5
    return [x/magnitude for x in embedding]
```

### Graph Traversal

**Finding related concepts:**
```python
def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
    # Find starting nodes matching query
    start_nodes = self._find_matching_nodes(query)
    
    # Perform BFS to find related concepts
    for node in start_nodes:
        neighbors = nx.bfs_tree(self.graph, node, depth_limit=2)
        # Score based on graph distance
        for neighbor in neighbors:
            score = 1.0 / (distance + 1)
            results.append({
                "node": neighbor,
                "similarity_score": score,
                "relationship_path": path
            })
    
    return sorted(results, key=lambda x: x["similarity_score"])[:top_k]
```

### Similarity Scoring

**Cosine Similarity:**
```python
similarity = cosine_similarity([query_embedding], [doc_embedding])[0]

# Only return results above threshold
if similarity > 0.7:
    results.append(document)
```

**Hybrid Scoring:**
```python
hybrid_score = (vector_similarity * 0.6) + (graph_similarity * 0.4)
```

## Performance Optimizations

1. **Embedding Cache**: Computed embeddings stored in memory
2. **Lazy Indexing**: Documents indexed only when first search performed
3. **Top-K Limiting**: Only process top results to limit LLM context
4. **Session Reuse**: Conversation context maintained across requests
5. **Background Indexing**: Can index new documents asynchronously

## Integration Points

### With Agentic Chat
```python
# RAG provides context for tool decisions
result = await agentic_assistant.chat(
    message=query,
    conversation_manager=conv_manager,
    file_path=uploaded_file
)

# Agentic assistant uses RAG for:
# - Understanding user intent
# - Selecting appropriate tools
# - Generating contextual responses
```

### With Evidence Management
```python
# Upload evidence with RAG analysis
# RAG extracts: control mappings, evidence type, compliance framework
await rag_service.analyze_document(file_path)
```

### With Compliance Reporting
```python
# Generate reports using RAG for:
# - Finding relevant controls
# - Mapping evidence to requirements
# - Generating executive summaries
```

## Example Use Cases

### Use Case 1: Compliance Question
```
User: "How should we implement multi-factor authentication for ISO 27001?"

RAG Process:
1. Vector search → finds documents about authentication, MFA, access control
2. Graph search → traces: ISO 27001 → Access Control → IAM → Audit
3. Hybrid → combines both with 0.6/0.4 weights
4. LLM → generates actionable answer with implementation steps

Response:
"For ISO 27001 compliance, implement MFA according to control A.9.4.2:
1. Implement MFA for all remote access
2. Use at least two authentication factors...
[Detailed response with sources cited]"
```

### Use Case 2: Evidence Upload
```
User: [Uploads PDF] "Analyze this access control policy"

RAG Process:
1. File saved to /storage/evidence/20251113_policy.pdf
2. Agentic assistant analyzes file content
3. Detects: Policy document, Access Control domain
4. Suggests control mappings and evidence type
5. Creates evidence record with metadata

Response:
"I've analyzed your access control policy document. 
Key findings:
- Aligns with ISO 27001 control A.9.1.1
- Contains MFA requirements (A.9.4.2)
- Covers user provisioning procedures
Would you like me to upload this as evidence for specific controls?"
```

### Use Case 3: Relationship Discovery
```
User: "What evidence do I need for NIST CSF identity management?"

RAG Process:
1. Graph search → NIST_CSF → ACCESS_CONTROL → IAM → AUDIT → AUDIT_REPORT
2. Vector search → finds related policy and training requirements
3. Combines both paths to comprehensive answer

Response:
"For NIST CSF PR.AC-1 (Identity Management), you'll need:

Required Evidence:
• Access control policies (POLICY_DOC)
• IAM system audit reports (AUDIT_REPORT)  
• User training records (TRAINING_RECORD)
• Penetration test results (SCAN_REPORT)

Related Controls: ISO 27001 A.9.1.1, A.9.4.2"
```

## Benefits of This RAG Implementation

1. **Accuracy**: Grounds responses in actual compliance knowledge base
2. **Traceability**: Every answer includes source citations
3. **Flexibility**: Multiple search strategies for different query types
4. **Extensibility**: Easy to add new frameworks and controls
5. **Performance**: Caching and optimizations for fast responses
6. **Multi-Modal**: Supports text, files, and voice input
7. **Conversational**: Maintains context across multiple turns
8. **Integrated**: Works seamlessly with evidence management and agentic tools

## Future Enhancements

1. **Document Ingestion Pipeline**: Automatically index uploaded evidence documents
2. **Fine-tuned Embeddings**: Train custom embeddings on compliance corpus
3. **Dynamic Graph Updates**: Learn new relationships from user interactions
4. **Multi-Language Support**: Embeddings and responses in multiple languages
5. **Advanced Retrieval**: Dense passage retrieval, re-ranking models
6. **Feedback Loop**: Learn from user ratings to improve search quality
