# Kubeflow Pipelines for GraphRAG

This directory contains a Kubeflow Pipelines (KFP v2) skeleton for orchestrating graph validation, metadata updates, loading, and evaluation gating.

## Pipeline Overview

The pipeline orchestrates the following steps:

1. **Validate Graph**: Run schema and invariant validation on `complete_graph.json`
2. **Update Metadata**: Generate/verify `graph_metadata.json` with SHA256 hash and statistics
3. **Load Graph**: Load validated graph into Neo4j (placeholder)
4. **Eval Gate**: Run evaluation harness and gate on correctness metrics (placeholder)

## Mapping to Existing Scripts

- `validate_graph_op` → `python graph/validate_graph.py complete_graph.json`
- `update_metadata_op` → `python scripts/update_graph_metadata.py --check`
- `load_graph_op` → `python graph_rag_api/scripts/load_graph.py` (placeholder)
- `eval_op` → `python eval/run_eval.py` (placeholder)

## Status

**This is a scaffold only.** The pipeline components are placeholders that demonstrate the intended orchestration flow. The existing FastAPI application and evaluation harness behavior is unchanged.

## Compilation

To compile the pipeline to YAML:

```bash
cd pipelines
pip install -r requirements.txt
python pipeline.py --compile
```

This generates `pipeline.yaml` which can be uploaded to a Kubeflow Pipelines instance.

