# Production-Grade GraphRAG for Kubernetes Incident Reasoning

This system provides deterministic, explainable reasoning over Kubernetes infrastructure incidents using an incident-centric knowledge graph.

Unlike black-box LLM or vector-based RAG systems, it enforces causal correctness, provenance grounding, and reproducible evaluation through structured graph traversal and rule-based retrieval.

## Problem Statement

Naive vector RAG fails for infrastructure incident reasoning due to three fundamental limitations:

1. **Ambiguous symptoms**: Queries like "kubelet crash" match multiple incidents with similar symptoms but different root causes. Vector similarity cannot distinguish between a race condition and a divide-by-zero error.

2. **Similar components**: Multiple incidents affect the same component (e.g., kubelet) but have distinct failure modes and root causes. Semantic similarity conflates unrelated incidents.

3. **Causal correctness**: Incident reasoning requires precise causal chains (component → failure mode → root cause), not just topical relevance. Vector search cannot enforce structural constraints.

This system answers questions such as:
- "What causes kubelet to crash with concurrent map writes?"
- "Why does the API server create invalid IP addresses when service name is empty?"
- "What incident involves kube-scheduler panic and division by zero?"

Each answer is grounded in explicit graph relationships with provenance, not inferred from embeddings.

## Core Idea: Deterministic GraphRAG

The system uses an incident-centric knowledge graph where:

- **Normalized node types** ensure consistent entity representation (incident, component, failure_mode, root_cause, trigger, artifact, concept).
- **Deterministic anchor extraction** maps natural language queries to graph entities using synonym mappings and explicit pattern matching, not embeddings.
- **Graph traversal** follows typed relationships (AFFECTS, EXHIBITS, CAUSED_BY, etc.) to find incident subgraphs.
- **Scoring** ranks incidents by anchor match strength and graph connectivity, not by vector similarity.

This system contains no trained models and performs no probabilistic inference. All retrieval, ranking, and answer generation are deterministic and rule-based. The same query produces the same results across runs, and every fact in the response can be traced to a specific graph edge with evidence references.

## Graph Data Model

### Node Types

- **incident**: First-class anchor representing a specific failure event (e.g., "128638", "124930").
- **component**: Kubernetes component affected by incidents (e.g., "kubelet", "kube-scheduler", "kube-apiserver").
- **failure_mode**: How the incident manifests (e.g., "crash", "panic", "oom", "degradation", "validation_error").
- **root_cause**: Underlying cause of the failure (e.g., "unsynchronized-concurrent-access", "division-by-zero", "validation-gaps").
- **trigger**: Event or condition that activates the incident (e.g., "pod-configuration", "feature-gate").
- **artifact**: Code artifacts involved (e.g., "containerMap", "ContainerMap.Add").
- **concept**: Abstract concepts for context (e.g., "concurrency-control", "scheduler-scoring-logic").

### Relationship Types

- **AFFECTS**: incident → component (which component is affected).
- **EXHIBITS**: incident → failure_mode (how the incident manifests).
- **CAUSED_BY**: incident → root_cause (underlying cause).
- **TRIGGERED_BY**: incident → trigger (activation condition).
- **USES**: component → artifact (code artifacts used by components).
- **INVOLVES**: incident → concept (contextual concepts, not causal).

Incidents are first-class anchors because they are the primary query target. The system retrieves incidents, not generic entities, and explains them through their relationships to components, failure modes, and root causes.

## Provenance & Grounding Guarantees

Every key factual claim (AFFECTS, EXHIBITS, CAUSED_BY, TRIGGERED_BY, USES) must have:

- **edge-level evidence_refs**: List of source IDs pointing to provenance entries.
- **sources**: Resolved source objects with kind (github_issue, doc, kep), title, URL, and reference (e.g., "kubernetes/kubernetes#128638").

The system enforces "no citation, no claim": the `/ask` endpoint filters out any Tier-1 fact that lacks `evidence_refs`. If critical facts (component, failure_mode, root_cause) are missing citations, the API returns a refusal response rather than emitting ungrounded claims. The loader validates that all required edges have `evidence_refs` before loading into Neo4j, ensuring data integrity at ingestion time.

## Answer Semantics (Tiering)

The system separates hard evidence from contextual information:

- **Tier 1 facts** (AFFECTS, EXHIBITS, CAUSED_BY, TRIGGERED_BY, USES): Causal relationships that appear in the main narrative and evidence bullets. These require citations.

- **Tier 2 context** (INVOLVES): Non-causal concepts that provide context but do not explain causality. These appear only in the `context_concepts` field, never in the summary or evidence bullets.

The `/ask` endpoint enforces this separation:
- `summary`: Single professionally formatted sentence using only Tier-1 facts.
- `evidence_bullets`: One bullet per Tier-1 fact with formatted text and provenance.
- `context_concepts`: Tier-2 facts listed separately, not interwoven with causal explanation.

Tier-2 concepts never appear in the causal narrative. This prevents concepts like "concurrency-control" from being presented as root causes when they are merely contextual.

## Evaluation & Safety Gates

The evaluation harness (`eval/run_eval.py`) enforces multiple correctness criteria:

- **Golden queries**: Curated test cases with expected incident IDs (`eval/golden_queries.jsonl`, `eval/golden_queries_hard.jsonl`).
- **Accuracy@k**: Top-1 correctness and recall@k metrics.
- **Negative-evidence assertions**: Queries can specify forbidden root causes, failure modes, components, or incidents. The eval fails if any forbidden item appears in the response.
- **Provenance enforcement**: Queries with `require_provenance: true` must have all Tier-1 facts cited. Uncited facts trigger eval failures.
- **Runbook-format enforcement**: Queries with `require_runbook_format: true` must have summary without Tier-2 concepts and evidence_bullets count matching tier1_facts count.

Unlike typical RAG evaluations that measure only accuracy, this harness enforces correctness through negative-evidence checks, provenance validation, and format constraints. The CI gate (`.github/workflows/eval.yml`) runs both eval files on every PR. Any regression (accuracy drop, negative-evidence violation, provenance failure, format violation) fails the build. This prevents silent degradation.

## Dataset Artifact Discipline

The graph dataset is treated as a versioned artifact:

- **complete_graph.json**: Canonical dataset file containing all entities, edges, and sources.
- **graph_metadata.json**: Metadata including SHA256 hash, node/edge counts, and provenance statistics.
- **SHA256 locking**: The loader verifies the graph file hash matches `graph_metadata.json` before loading. Mismatch aborts the load.
- **Schema validation**: `graph/validate_graph.py` checks unique node IDs, required fields, valid edge endpoints, and source validity.
- **Invariant validation**: Enforces graph rules (every incident has exactly 1 EXHIBITS → failure_mode, 1 CAUSED_BY → root_cause, >=1 AFFECTS → component).

The metadata script (`scripts/update_graph_metadata.py`) generates metadata deterministically. The `--check` flag verifies metadata matches computed values, failing on drift.

This prevents silent data corruption: graph changes are detected by hash mismatch, schema violations are caught before load, and invariant violations fail validation.

## System Architecture

The system follows a deterministic pipeline:

1. **FastAPI API**: REST API with `/query`, `/explain`, and `/ask` endpoints.
2. **Neo4j**: Graph database storing entities and relationships with both typed and generic relationship formats for compatibility.
3. **Retrieval Service**: Anchor extraction, graph traversal, fact extraction with deterministic deduplication.
4. **Ask Service**: Runbook-grade answer generation with tiering, provenance filtering, and evidence bullet formatting.
5. **Eval Harness**: Evaluation against golden queries with multiple correctness checks.
6. **CI Gate**: Automated evaluation on PRs with Neo4j service container.

The graph loader is deterministic and idempotent: it clears the graph, validates schema/invariants/hash, then loads entities and relationships in batch operations.

There is no LLM dependency in the current implementation. All retrieval, ranking, and formatting is rule-based and deterministic. This is by design: LLM integration (Phase 4) will be additive, not replacing the deterministic core.

## How to Run Locally

### Prerequisites

- Python 3.11+
- Neo4j 5.x (Docker or local installation)
- Neo4j credentials (default: `neo4j`/`testpassword`)

### Start Neo4j

Using Docker:
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/testpassword \
  neo4j:5
```

Or use a local Neo4j installation with authentication configured.

### Load Graph

```bash
cd graph_rag_api
python scripts/load_graph.py
```

This will:
1. Validate schema and invariants
2. Verify SHA256 hash against metadata
3. Clear existing graph
4. Load entities and relationships
5. Print verification statistics

### Run API

```bash
cd graph_rag_api
uvicorn app.main:app --port 8000
```

The API will be available at `http://localhost:8000`. Endpoints:
- `POST /query`: Graph query with anchor extraction
- `GET /explain/{incident_id}`: Explain a specific incident
- `POST /ask`: Ask a question, get runbook-grade answer
- `GET /debug/stats`: Graph statistics

### Run Evaluations

```bash
# Basic eval set
python eval/run_eval.py --gold eval/golden_queries.jsonl --k 5 --base-url http://127.0.0.1:8000

# Hard eval set
python eval/run_eval.py --gold eval/golden_queries_hard.jsonl --k 5 --base-url http://127.0.0.1:8000
```

Both should report full accuracy with zero negative-evidence, provenance, or format violations.

### Update Graph Metadata

After modifying `complete_graph.json`:
```bash
python scripts/update_graph_metadata.py
```

To verify metadata is current:
```bash
python scripts/update_graph_metadata.py --check
```

## Roadmap

**Phase 1 (Complete)**: Deterministic GraphRAG with evaluation and CI gates.
- Incident-centric knowledge graph
- Deterministic anchor extraction and retrieval
- Provenance enforcement ("no citation, no claim")
- Fact tiering (Tier-1 evidence vs Tier-2 context)
- Runbook-grade answer formatting
- Comprehensive evaluation harness
- CI gate preventing regressions
- Dataset artifact discipline (hash locking, validation)

**Phase 2 (Planned)**: Kubeflow pipeline for ingestion, validation, evaluation, and gating.
- Automated graph ingestion from sources
- Validation pipeline (schema, invariants, hash)
- Evaluation pipeline with gating decisions
- Metadata generation and versioning
- Integration with ML metadata store

**Phase 3 (Optional)**: Hybrid vector + graph retrieval.
- Vector embeddings for semantic similarity and recall expansion
- Graph structure remains the authoritative grounding layer for causal correctness
- Hybrid ranking combines both signals, with graph facts as the source of truth
- Evaluation to measure improvement over graph-only while maintaining correctness guarantees

**Phase 4 (Future)**: LLM-backed narrative with strict grounding.
- LLM generates natural language from structured facts
- Strict grounding: every claim must map to a cited fact
- Evaluation to detect hallucination or ungrounded claims
- Fallback to deterministic templates if grounding fails

Each phase builds on the deterministic foundation. LLM integration will not replace the structured retrieval core; it will enhance presentation while maintaining correctness guarantees.

