# Kubeflow Pipelines for GraphRAG

This directory contains a Kubeflow Pipelines (KFP v2) skeleton for orchestrating graph validation, metadata updates, loading, and evaluation gating.

## Pipeline Overview

The pipeline orchestrates the following steps:

1. **Validate Graph**: Run schema and invariant validation on `complete_graph.json`
2. **Update Metadata**: Generate/verify `graph_metadata.json` with SHA256 hash and statistics
3. **Eval Gate**: Run evaluation harness against both golden query files and fail on any regressions
4. **Load Graph**: Load validated graph into Neo4j (placeholder, future work)

**Note**: This pipeline assumes that Neo4j and the FastAPI service are externally available and reachable at the provided `api_base_url`. The next increment will deploy these services within the pipeline when running on a cluster with service support.

## Mapping to Existing Scripts

- `validate_graph_op` → `python graph/validate_graph.py complete_graph.json`
- `update_metadata_op` → `python scripts/update_graph_metadata.py --check`
- `eval_gate_op` → `python eval/run_eval.py --gold eval/golden_queries.jsonl --k 5 --base-url <api_base_url>` and `python eval/run_eval.py --gold eval/golden_queries_hard.jsonl --k 5 --base-url <api_base_url>`
- `load_graph_op` → `python graph_rag_api/scripts/load_graph.py` (placeholder)

## Status

The pipeline includes working implementations for graph validation, metadata verification, and evaluation gating. The load graph step remains a placeholder for future work. The existing FastAPI application and evaluation harness behavior is unchanged. The pipeline assumes Neo4j and API services are externally available; future work will deploy these services within the pipeline.

## Compilation

To compile the pipeline to YAML:

```bash
cd pipelines
pip install -r requirements.txt
python pipeline.py --compile
```

This generates `pipeline.yaml` which can be uploaded to a Kubeflow Pipelines instance.

