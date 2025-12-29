# GraphRAG API

Production-grade FastAPI service for GraphRAG retrieval over Neo4j graph database.

## Features

- **Anchor Entity Lookup**: Finds relevant entities from natural language questions using token matching
- **Bounded Graph Expansion**: Expands subgraph from anchors with configurable depth and relationship filtering
- **Fact Extraction**: Converts graph relationships into structured facts for LLM grounding
- **Evidence Collection**: Identifies relevant incident IDs from the expanded subgraph
- **Production-Ready**: Modular architecture, structured logging, error handling, connection pooling

## Architecture

```
graph_rag_api/
├── app/
│   ├── main.py              # FastAPI app + routing
│   ├── config.py            # Settings from environment
│   ├── logging.py           # Structured logging
│   ├── db/
│   │   └── neo4j_client.py  # Neo4j driver lifecycle
│   ├── services/
│   │   └── retrieval.py     # Core retrieval logic
│   ├── models/
│   │   └── api.py           # Pydantic request/response models
│   └── utils/
│       └── text.py          # Text tokenization
└── scripts/
    └── sanity_queries.cypher # Debug queries
```

## Prerequisites

- Python 3.9+
- Neo4j 4.x+ with APOC plugin installed
- Graph data imported into Neo4j (nodes labeled `:Entity`, relationships with `type` property)

## Installation

1. **Clone and navigate to the project:**
   ```bash
   cd graph_rag_api
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **If you encounter numpy/pandas compatibility errors** (ValueError: numpy.dtype size changed):
   ```bash
   # Fix binary incompatibility by reinstalling compatible versions
   pip uninstall -y numpy pandas
   pip install "numpy>=1.24.0,<2.0.0" "pandas>=2.0.0,<3.0.0"
   ```
   
   This happens because the neo4j driver imports pandas as an optional dependency, and pandas must be compiled against a compatible numpy version.

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Neo4j connection details
   ```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DB=neo4j

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Retrieval Defaults (can be overridden per request)
DEFAULT_MAX_HOPS=2
DEFAULT_MAX_PATHS=300
DEFAULT_MAX_FACTS=120
DEFAULT_MAX_ANCHORS=15
```

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## CI Eval Gate

This repository includes a GitHub Actions CI workflow (`.github/workflows/eval.yml`) that runs on every pull request to `main` and every push to `main`. The workflow:

1. **Spins up Neo4j**: Uses a Neo4j 5 service container
2. **Loads the graph**: Runs `scripts/load_graph.py` to load `complete_graph.json` into Neo4j
3. **Starts the API**: Launches the FastAPI server
4. **Runs evaluations**: Executes both eval sets:
   - `eval/golden_queries.jsonl`
   - `eval/golden_queries_hard.jsonl`
5. **Fails on regression**: If either eval set fails (any query doesn't match expected incident IDs), the workflow fails and blocks the PR

**PRs must keep eval green** - any retrieval regression will cause the CI to fail. This ensures that changes to retrieval logic, normalization, or anchor filtering don't degrade retrieval accuracy.

To run the eval locally (requires Neo4j running):
```bash
# Load graph
python graph_rag_api/scripts/load_graph.py

# Start API (in another terminal)
uvicorn graph_rag_api.app.main:app --port 8000

# Run eval
python eval/run_eval.py --gold eval/golden_queries.jsonl --k 5
python eval/run_eval.py --gold eval/golden_queries_hard.jsonl --k 5
```

## API Endpoints

### POST /explain

Explain an incident by retrieving and categorizing its relationships.

**Request:**
```json
{
  "incident_id": "124930",
  "include_facts": true
}
```

**Response:**
```json
{
  "incident_id": "124930",
  "severity": "high",
  "affects": ["kube-scheduler"],
  "failure_modes": ["panic"],
  "root_causes": ["division-by-zero"],
  "triggers": ["pod-configuration"],
  "concepts": ["scheduler-scoring-logic", "edge-case-handling"],
  "artifacts_direct": [],
  "artifacts_derived": ["containerMap", "ContainerMap.Add"],
  "artifacts": ["containerMap", "ContainerMap.Add"],
  "facts": [
    {"from": "124930", "rel": "AFFECTS", "to": "kube-scheduler"},
    {"from": "124930", "rel": "EXHIBITS", "to": "panic"},
    {"from": "124930", "rel": "CAUSED_BY", "to": "division-by-zero"}
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "124930"}'
```

**Parameters:**
- `incident_id` (required): The ID of the incident to explain
- `include_facts` (optional, default: true): Whether to include facts (relationships) in the response

**Errors:**
- `404`: Incident not found
- `500`: Internal server error

### POST /ask

Ask a question and get a deterministic grounded answer using /query + /explain logic.

**Request:**
```json
{
  "question": "kubelet crash concurrent map writes",
  "max_incidents": 1,
  "max_facts": 12
}
```

**Response:**
```json
{
  "question": "kubelet crash concurrent map writes",
  "answer": "Most relevant incident is 128638 affecting kubelet. It exhibits crash caused by unsynchronized-concurrent-access. Relevant artifacts: containerMap, ContainerMap.Add.",
  "evidence": {
    "incident_ids": ["128638"]
  },
  "key_facts": [
    {"from": "128638", "rel": "AFFECTS", "to": "kubelet"},
    {"from": "128638", "rel": "EXHIBITS", "to": "crash"},
    {"from": "128638", "rel": "CAUSED_BY", "to": "unsynchronized-concurrent-access"}
  ],
  "incident_cards": [
    {
      "incident_id": "128638",
      "severity": "high",
      "affects": ["kubelet"],
      "failure_modes": ["crash"],
      "root_causes": ["unsynchronized-concurrent-access"],
      "triggers": [],
      "concepts": [],
      "artifacts_direct": [],
      "artifacts_derived": ["containerMap", "ContainerMap.Add"],
      "artifacts": ["containerMap", "ContainerMap.Add"],
      "facts": []
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "kubelet crash concurrent map writes",
    "max_incidents": 1,
    "max_facts": 12
  }'
```

**Parameters:**
- `question` (required): The question to ask
- `max_incidents` (optional, default: 1): Maximum incidents to include
- `max_facts` (optional, default: 12): Maximum key facts to return

**Errors:**
- `500`: Internal server error

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok"}
```

### Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What incidents involve kubelet crashes?",
    "max_hops": 2,
    "max_paths": 300,
    "max_facts": 120
  }'
```

Response:
```json
{
  "question": "What incidents involve kubelet crashes?",
  "anchors": [
    {"id": "kubelet", "type": "component"},
    {"id": "crash", "type": "failure_mode"}
  ],
  "facts": [
    {"from": "128638", "rel": "AFFECTS", "to": "kubelet"},
    {"from": "128638", "rel": "EXHIBITS", "to": "crash"},
    ...
  ],
  "evidence": {
    "incident_ids": ["128638", ...]
  },
  "stats": {
    "node_count": 45,
    "rel_count": 120
  }
}
```

## Sample Query Ideas

### Concurrency Incidents
```json
{
  "question": "What incidents are caused by concurrency issues?",
  "max_hops": 2
}
```

### Scheduler Panic
```json
{
  "question": "Find incidents where kube-scheduler panics",
  "max_hops": 2
}
```

### Conntrack OOM
```json
{
  "question": "What causes out of memory issues with conntrack?",
  "max_hops": 2
}
```

### Component Failures
```json
{
  "question": "Show me incidents affecting etcd",
  "max_hops": 2
}
```

## How It Works

### 1. Anchor Lookup

- Tokenizes the question (lowercase, split on whitespace/punctuation, filter tokens < 4 chars)
- Searches `Entity.id` for token matches (case-insensitive substring)
- Filters to entity types: `component`, `root_cause`, `failure_mode`, `concept`
- Weights by type: component (3), root_cause/failure_mode (2), concept (1)
- Returns top 15 anchors

### 2. Graph Expansion

- Uses APOC `apoc.path.expandConfig` for bounded traversal
- Relationship filter: incident-centric policy
  - Allows incoming `INVOLVES` (pull incidents that involve concepts/artifacts)
  - Prevents outgoing `INVOLVES` expansion (avoids concept explosion)
  - Allows other relationship types more freely
- Configurable depth (default: 2 hops)
- BFS traversal with path limit (default: 300 paths)

### 3. Fact Extraction

- Converts relationships to fact tuples: `{from, rel, to}`
- Deduplicates relationships
- Limits to `max_facts` (default: 120)
- Extracts incident IDs from nodes in subgraph

### 4. Response Assembly

- Returns anchors, facts, evidence (incident IDs), and statistics

## Relationship Filter Policy

The default relationship filter uses an incident-centric approach:

```
AFFECTS<|CAUSED_BY<|EXHIBITS<|TRIGGERED_BY<|ACTIVATES<|LEADS_TO>|USES>|DEPENDS_ON>|INVOLVES<
```

- `INVOLVES<`: Only incoming edges (pull incidents involving concepts/artifacts, don't expand through concepts)
- Other relationships: More permissive (allows bidirectional or directional as needed)

This prevents concept explosion while still retrieving relevant incident connections.

## Debugging

### Check Neo4j Connection

```bash
# Test health endpoint
curl http://localhost:8000/health
```

### Run Sanity Queries

Use queries in `scripts/sanity_queries.cypher` in Neo4j Browser to verify:
- Entity counts and types
- Relationship types
- APOC availability
- Sample anchor lookups
- Path expansion behavior

### View Logs

The application uses structured logging. Logs include:
- Connection status
- Query processing steps
- Anchor discovery results
- Graph expansion statistics
- Errors and warnings

## Requirements

- FastAPI 0.109.0
- Neo4j Python driver 5.15.0
- Pydantic 2.5.3
- Uvicorn (for serving)

## Neo4j Graph Schema

Expected schema:

**Nodes:**
- Label: `:Entity`
- Properties:
  - `id` (string, unique): Entity identifier
  - `type` (string): One of `["component", "concept", "artifact", "incident", "root_cause", "trigger", "failure_mode"]`
  - Optional: `severity`, `category`, `layer`, `version`, etc.

**Relationships:**
- Any relationship type
- Property: `type` (string): One of `["INVOLVES", "USES", "LEADS_TO", "AFFECTS", "CAUSED_BY", "TRIGGERED_BY", "ACTIVATES", "EXHIBITS", "DEPENDS_ON"]`

## License

MIT

