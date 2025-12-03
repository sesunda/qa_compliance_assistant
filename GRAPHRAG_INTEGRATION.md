# GraphRAG Integration for QA Compliance Assistant
## Phase 2: Knowledge Graph Enhancement

---

## Overview

**GraphRAG** will enhance compliance analysis by building a knowledge graph of relationships between:
- **Controls** ↔ Evidence ↔ Frameworks
- **Projects** ↔ Assessments ↔ Findings
- **Users** ↔ Agencies ↔ Reviews

This enables:
1. **Evidence Reuse Discovery**: "Evidence for Control 3 also satisfies Controls 7, 12"
2. **Gap Analysis**: "Controls missing evidence", "Underutilized evidence"
3. **Compliance Insights**: "High-impact controls with weak evidence"
4. **Relationship Patterns**: "Evidence types most effective for IM8 domains"

---

## Architecture

### Option 1: Microsoft GraphRAG (Recommended)
**Best for**: Azure-native, minimal infrastructure

```
┌─────────────────────────────────────────────────┐
│           QA Compliance Assistant                │
│  ┌──────────────────────────────────────────┐  │
│  │     Agent Framework Assistant             │  │
│  │  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Tool Calls │→ │ GraphRAG Analyzer  │  │  │
│  │  └────────────┘  └─────────┬──────────┘  │  │
│  └──────────────────────────────┼────────────┘  │
└─────────────────────────────────┼───────────────┘
                                  ▼
┌─────────────────────────────────────────────────┐
│         Microsoft GraphRAG Engine                │
│  ┌──────────────┐  ┌──────────────────────────┐│
│  │ Knowledge    │  │  Graph Construction       ││
│  │ Extraction   │→ │  (Entities + Relations)   ││
│  └──────────────┘  └───────────┬──────────────┘│
└─────────────────────────────────┼───────────────┘
                                  ▼
┌─────────────────────────────────────────────────┐
│          Azure Cosmos DB (Gremlin API)           │
│  - Control nodes (id, name, domain)              │
│  - Evidence nodes (id, title, type)              │
│  - Edges: SATISFIES, RELATES_TO, SUPPORTS       │
└─────────────────────────────────────────────────┘
```

### Option 2: Neo4j Graph Database
**Best for**: Advanced graph analytics, visualization

```
PostgreSQL (existing)    Neo4j Graph Database
─────────────────────    ────────────────────
Controls                 (:Control {id, domain})
Evidence        sync→    (:Evidence {id, type})
Projects                 (:Project {id, name})
                         
                         Relationships:
                         (Evidence)-[:SATISFIES]->(Control)
                         (Evidence)-[:RELATES_TO]->(Evidence)
                         (Control)-[:PART_OF]->(Project)
```

---

## Implementation Plan

### Week 1: Graph Schema Design

**Define Node Types:**
```cypher
// Neo4j Cypher schema
CREATE CONSTRAINT control_id IF NOT EXISTS
FOR (c:Control) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT evidence_id IF NOT EXISTS
FOR (e:Evidence) REQUIRE e.id IS UNIQUE;

// Node: Control
CREATE (c:Control {
  id: 3,
  name: "Network Segmentation",
  domain: "IM8-02",
  status: "implemented",
  priority: "high"
})

// Node: Evidence
CREATE (e:Evidence {
  id: 15,
  title: "Firewall Configuration",
  type: "configuration_screenshot",
  verification_status: "approved",
  quality_score: 0.85
})

// Relationship: Evidence satisfies Control
CREATE (e)-[:SATISFIES {
  confidence: 0.92,
  created_at: datetime(),
  verified: true
}]->(c)
```

**Define Relationship Types:**
- `SATISFIES`: Evidence → Control (primary compliance link)
- `RELATES_TO`: Evidence → Evidence (similar/complementary)
- `PART_OF`: Control → Project
- `SUBMITTED_BY`: Evidence → User
- `REVIEWED_BY`: Evidence → User
- `CONTRIBUTES_TO`: Control → Assessment

### Week 2: Data Sync Service

**Create GraphRAG sync service:**

```python
# api/src/services/graphrag_sync.py

from neo4j import GraphDatabase
from api.src.models import Control, Evidence, Project
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class GraphRAGSyncService:
    """Sync PostgreSQL data to Neo4j graph database"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def sync_controls(self, db: Session):
        """Sync all controls to graph"""
        controls = db.query(Control).all()
        
        with self.driver.session() as session:
            for control in controls:
                session.run(
                    """
                    MERGE (c:Control {id: $id})
                    SET c.name = $name,
                        c.domain = $domain,
                        c.status = $status,
                        c.priority = $priority,
                        c.updated_at = datetime()
                    """,
                    id=control.id,
                    name=control.name,
                    domain=control.im8_domain,
                    status=control.status,
                    priority=control.priority
                )
        
        logger.info(f"Synced {len(controls)} controls to graph")
    
    def sync_evidence(self, db: Session):
        """Sync all evidence and relationships to graph"""
        from api.src.models import Evidence
        
        evidence_list = db.query(Evidence).all()
        
        with self.driver.session() as session:
            for evidence in evidence_list:
                # Create evidence node
                session.run(
                    """
                    MERGE (e:Evidence {id: $id})
                    SET e.title = $title,
                        e.type = $type,
                        e.status = $status,
                        e.quality_score = $quality_score,
                        e.updated_at = datetime()
                    """,
                    id=evidence.id,
                    title=evidence.title,
                    type=evidence.evidence_type,
                    status=evidence.verification_status,
                    quality_score=evidence.quality_score or 0.5
                )
                
                # Create SATISFIES relationship to control
                if evidence.control_id:
                    session.run(
                        """
                        MATCH (e:Evidence {id: $evidence_id})
                        MATCH (c:Control {id: $control_id})
                        MERGE (e)-[r:SATISFIES]->(c)
                        SET r.confidence = $confidence,
                            r.updated_at = datetime()
                        """,
                        evidence_id=evidence.id,
                        control_id=evidence.control_id,
                        confidence=evidence.quality_score or 0.5
                    )
        
        logger.info(f"Synced {len(evidence_list)} evidence to graph")
    
    def find_related_evidence(self, evidence_id: int, limit: int = 5) -> list:
        """Find evidence related to given evidence using graph patterns"""
        
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e1:Evidence {id: $evidence_id})-[:SATISFIES]->(c:Control)
                MATCH (e2:Evidence)-[:SATISFIES]->(c)
                WHERE e2.id <> $evidence_id
                RETURN e2.id AS evidence_id, 
                       e2.title AS title,
                       c.id AS control_id,
                       c.name AS control_name,
                       COUNT(c) AS shared_controls
                ORDER BY shared_controls DESC
                LIMIT $limit
                """,
                evidence_id=evidence_id,
                limit=limit
            )
            
            return [dict(record) for record in result]
    
    def find_evidence_reuse_opportunities(self, evidence_id: int) -> list:
        """
        Find controls that could be satisfied by existing evidence
        Uses graph patterns to find similar controls
        """
        
        with self.driver.session() as session:
            result = session.run(
                """
                // Get the control this evidence satisfies
                MATCH (e:Evidence {id: $evidence_id})-[:SATISFIES]->(c1:Control)
                
                // Find similar controls in same domain
                MATCH (c2:Control)
                WHERE c2.domain = c1.domain 
                  AND c2.id <> c1.id
                  AND NOT EXISTS((e)-[:SATISFIES]->(c2))
                
                // Check if other evidence for c1 also satisfies c2
                MATCH (other_evidence:Evidence)-[:SATISFIES]->(c1)
                MATCH (other_evidence)-[:SATISFIES]->(c2)
                
                WITH c2, COUNT(DISTINCT other_evidence) AS pattern_count
                ORDER BY pattern_count DESC
                
                RETURN c2.id AS control_id,
                       c2.name AS control_name,
                       c2.domain AS domain,
                       pattern_count AS confidence_score
                LIMIT 5
                """,
                evidence_id=evidence_id
            )
            
            return [dict(record) for record in result]
    
    def get_compliance_insights(self, project_id: int) -> dict:
        """
        Generate compliance insights using graph analytics
        """
        
        with self.driver.session() as session:
            # Controls without evidence
            no_evidence = session.run(
                """
                MATCH (c:Control)-[:PART_OF]->(:Project {id: $project_id})
                WHERE NOT EXISTS((e:Evidence)-[:SATISFIES]->(c))
                RETURN c.id AS control_id, c.name AS control_name
                """,
                project_id=project_id
            )
            
            # High-priority controls with low-quality evidence
            weak_evidence = session.run(
                """
                MATCH (c:Control {priority: 'high'})-[:PART_OF]->(:Project {id: $project_id})
                MATCH (e:Evidence)-[:SATISFIES]->(c)
                WHERE e.quality_score < 0.6
                RETURN c.id AS control_id, 
                       c.name AS control_name,
                       AVG(e.quality_score) AS avg_quality
                ORDER BY avg_quality ASC
                """,
                project_id=project_id
            )
            
            # Underutilized evidence (can satisfy more controls)
            underutilized = session.run(
                """
                MATCH (e:Evidence)-[:SATISFIES]->(c:Control)-[:PART_OF]->(:Project {id: $project_id})
                WITH e, COUNT(c) AS control_count
                WHERE control_count = 1 AND e.quality_score > 0.8
                RETURN e.id AS evidence_id,
                       e.title AS evidence_title,
                       e.quality_score AS quality
                ORDER BY e.quality_score DESC
                LIMIT 10
                """,
                project_id=project_id
            )
            
            return {
                "controls_without_evidence": [dict(r) for r in no_evidence],
                "high_priority_weak_evidence": [dict(r) for r in weak_evidence],
                "underutilized_evidence": [dict(r) for r in underutilized]
            }
    
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()


# Global instance
graphrag_sync = GraphRAGSyncService(
    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    user=os.getenv("NEO4J_USER", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password")
)
```

### Week 3: Agent Framework GraphRAG Tools

**Add GraphRAG tools to Agent Framework:**

```python
# Add to agent_framework_assistant.py

@Tool.from_function
async def find_evidence_reuse_opportunities(
    evidence_id: int
) -> Dict[str, Any]:
    """
    Find controls that could be satisfied by existing evidence.
    Uses knowledge graph to discover reuse patterns.
    
    Args:
        evidence_id: Evidence ID to analyze for reuse
    
    Returns:
        List of suggested controls with confidence scores
    """
    try:
        from api.src.services.graphrag_sync import graphrag_sync
        
        opportunities = graphrag_sync.find_evidence_reuse_opportunities(evidence_id)
        
        return {
            "success": True,
            "evidence_id": evidence_id,
            "opportunities": opportunities,
            "count": len(opportunities)
        }
    except Exception as e:
        logger.error(f"GraphRAG reuse analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@Tool.from_function
async def get_compliance_insights(
    project_id: int
) -> Dict[str, Any]:
    """
    Generate compliance insights using graph analytics.
    Identifies gaps, weak areas, and optimization opportunities.
    
    Args:
        project_id: Project ID to analyze
    
    Returns:
        Comprehensive insights with actionable recommendations
    """
    try:
        from api.src.services.graphrag_sync import graphrag_sync
        
        insights = graphrag_sync.get_compliance_insights(project_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"GraphRAG insights failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

### Week 4: Background Sync + Testing

**Automated sync on data changes:**

```python
# api/src/models.py (add event listeners)

from sqlalchemy import event
from api.src.services.graphrag_sync import graphrag_sync

@event.listens_for(Evidence, 'after_insert')
@event.listens_for(Evidence, 'after_update')
def sync_evidence_to_graph(mapper, connection, target):
    """Auto-sync evidence changes to graph"""
    try:
        graphrag_sync.sync_evidence_single(target)
    except Exception as e:
        logger.warning(f"GraphRAG sync failed: {e}")

@event.listens_for(Control, 'after_insert')
@event.listens_for(Control, 'after_update')
def sync_control_to_graph(mapper, connection, target):
    """Auto-sync control changes to graph"""
    try:
        graphrag_sync.sync_control_single(target)
    except Exception as e:
        logger.warning(f"GraphRAG sync failed: {e}")
```

---

## Deployment

### Neo4j Setup (Azure)

```bash
# Option 1: Azure Container Instance (quickest)
az container create \
  --resource-group rg-qca-dev \
  --name neo4j-qca-dev \
  --image neo4j:5.14.0 \
  --ports 7474 7687 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    NEO4J_AUTH=neo4j/yourpassword \
    NEO4J_dbms_memory_pagecache_size=1G \
    NEO4J_dbms_memory_heap_max__size=2G

# Option 2: Azure Cosmos DB with Gremlin API (managed)
# Higher cost but fully managed, no maintenance
az cosmosdb create \
  --name qca-graph-dev \
  --resource-group rg-qca-dev \
  --capabilities EnableGremlin
```

### Environment Variables

Add to `api/.env.production`:

```bash
# Neo4j Graph Database
NEO4J_URI=bolt://neo4j-qca-dev.westus2.azurecontainer.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# GraphRAG Feature Flag
GRAPHRAG_ENABLED=false  # Enable after testing
```

---

## Testing GraphRAG

```python
# test_graphrag.py

import asyncio
from api.src.services.graphrag_sync import graphrag_sync
from api.src.database import SessionLocal

async def test_graphrag():
    db = SessionLocal()
    
    # Test 1: Sync data
    print("Syncing controls...")
    graphrag_sync.sync_controls(db)
    
    print("Syncing evidence...")
    graphrag_sync.sync_evidence(db)
    
    # Test 2: Find related evidence
    print("\nFinding related evidence for evidence_id=15...")
    related = graphrag_sync.find_related_evidence(15)
    print(f"Found {len(related)} related evidence")
    
    # Test 3: Evidence reuse opportunities
    print("\nFinding reuse opportunities...")
    opportunities = graphrag_sync.find_evidence_reuse_opportunities(15)
    print(f"Found {len(opportunities)} reuse opportunities")
    
    # Test 4: Compliance insights
    print("\nGenerating compliance insights...")
    insights = graphrag_sync.get_compliance_insights(project_id=1)
    print(f"Controls without evidence: {len(insights['controls_without_evidence'])}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_graphrag())
```

---

## Expected Benefits

### Before GraphRAG
- Evidence reuse: Manual review required
- Gap analysis: SQL queries, limited insights
- Relationship discovery: Not available
- Compliance optimization: Reactive

### After GraphRAG
- ✅ Evidence reuse: Automated suggestions (5-10 per evidence)
- ✅ Gap analysis: Graph-powered insights
- ✅ Relationship discovery: Graph patterns reveal hidden connections
- ✅ Compliance optimization: Proactive recommendations

### Performance Impact
- Graph query response: <100ms
- Sync overhead: <50ms per insert/update
- Storage: +500MB for graph database
- Total cost: +$20-30/month (Neo4j Container Instance)

---

## Next Steps

1. **Complete Phase 1** (Agent Framework migration)
2. **Deploy Neo4j** (Azure Container Instance)
3. **Implement GraphRAG sync service**
4. **Add GraphRAG tools to Agent Framework**
5. **Test and validate insights**
6. **Enable in production**

**Timeline**: 4 weeks after Phase 1 stable
