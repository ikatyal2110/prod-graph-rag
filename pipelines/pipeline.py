#!/usr/bin/env python3
"""
Kubeflow Pipelines v2 definition for GraphRAG graph validation and loading.

This pipeline orchestrates:
1. Graph validation (schema + invariants)
2. Metadata update/verification
3. Evaluation gating (runs both golden query files, fails on regressions)
4. Graph loading into Neo4j (placeholder)

Usage:
    python pipeline.py --compile    # Compile to pipeline.yaml
"""

import argparse
from pathlib import Path

try:
    from kfp import dsl
    from kfp.compiler import Compiler
except ImportError:
    print("Error: kfp library required. Install with: pip install -r requirements.txt", file=__import__('sys').stderr)
    exit(1)


@dsl.component(
    base_image="python:3.11-slim",
)
def validate_graph_op():
    """Validate graph schema and invariants."""
    import subprocess
    import sys
    
    result = subprocess.run(
        ["python", "/workspace/pipelines/components/validate_graph.py"],
        cwd="/workspace",
    )
    sys.exit(result.returncode)


@dsl.component(
    base_image="python:3.11-slim",
)
def update_metadata_op():
    """Update/verify graph metadata."""
    import subprocess
    import sys
    
    result = subprocess.run(
        ["python", "/workspace/pipelines/components/update_metadata.py"],
        cwd="/workspace",
    )
    sys.exit(result.returncode)


@dsl.component(
    base_image="python:3.11-slim",
)
def load_graph_op():
    """Load graph into Neo4j (placeholder)."""
    print("TODO: load graph into Neo4j")


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=["requests>=2.31.0"],
)
def eval_gate_op(api_base_url: str = "http://127.0.0.1:8000"):
    """Run evaluation gate against API."""
    import subprocess
    import sys
    from pathlib import Path
    
    workspace = Path("/workspace")
    eval_script = workspace / "eval" / "run_eval.py"
    golden_queries = workspace / "eval" / "golden_queries.jsonl"
    golden_queries_hard = workspace / "eval" / "golden_queries_hard.jsonl"
    
    if not eval_script.exists():
        print(f"Error: Eval script not found: {eval_script}", file=sys.stderr)
        sys.exit(1)
    
    if not golden_queries.exists():
        print(f"Error: Golden queries file not found: {golden_queries}", file=sys.stderr)
        sys.exit(1)
    
    if not golden_queries_hard.exists():
        print(f"Error: Hard golden queries file not found: {golden_queries_hard}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Running evaluation gate against API: {api_base_url}")
    print("=" * 70)
    
    # Run first eval set
    print("\nRunning eval/golden_queries.jsonl...")
    result1 = subprocess.run(
        [sys.executable, str(eval_script), "--gold", str(golden_queries), "--k", "5", "--base-url", api_base_url],
        cwd=str(workspace),
    )
    
    if result1.returncode != 0:
        print(f"\n✗ Evaluation failed on golden_queries.jsonl (exit code {result1.returncode})", file=sys.stderr)
        sys.exit(1)
    
    # Run second eval set
    print("\nRunning eval/golden_queries_hard.jsonl...")
    result2 = subprocess.run(
        [sys.executable, str(eval_script), "--gold", str(golden_queries_hard), "--k", "5", "--base-url", api_base_url],
        cwd=str(workspace),
    )
    
    if result2.returncode != 0:
        print(f"\n✗ Evaluation failed on golden_queries_hard.jsonl (exit code {result2.returncode})", file=sys.stderr)
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Evaluation gate passed - all queries succeeded")
    print("=" * 70)


@dsl.pipeline(
    name="graphrag-validation-pipeline",
    description="Validate, update metadata, eval gate graph artifact"
)
def graphrag_pipeline(api_base_url: str = "http://127.0.0.1:8000"):
    """Main pipeline definition."""
    
    # Step 1: Validate graph
    validate_task = validate_graph_op()
    
    # Step 2: Update/verify metadata (depends on validation)
    metadata_task = update_metadata_op()
    metadata_task.after(validate_task)
    
    # Step 3: Run eval gate (depends on validate + metadata)
    # Assumes API and Neo4j are externally available at api_base_url
    eval_task = eval_gate_op(api_base_url=api_base_url)
    eval_task.after(metadata_task)
    
    # Step 4: Load graph (placeholder, future work)
    load_task = load_graph_op()
    load_task.after(eval_task)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GraphRAG Kubeflow Pipeline")
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile pipeline to YAML"
    )
    args = parser.parse_args()
    
    if args.compile:
        pipeline_file = Path(__file__).parent / "pipeline.yaml"
        Compiler().compile(graphrag_pipeline, str(pipeline_file))
        print(f"Pipeline compiled to: {pipeline_file}")
    else:
        print("Use --compile to generate pipeline.yaml")
        print("Example: python pipeline.py --compile")


if __name__ == "__main__":
    main()

