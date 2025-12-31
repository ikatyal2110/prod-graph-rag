#!/usr/bin/env python3
"""
Kubeflow Pipelines v2 definition for GraphRAG graph validation and loading.

This pipeline orchestrates:
1. Graph validation (schema + invariants)
2. Metadata update/verification
3. Graph loading into Neo4j (placeholder)
4. Evaluation gating (placeholder)

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
)
def eval_op():
    """Run evaluation gate (placeholder)."""
    print("TODO: run eval gate")


@dsl.pipeline(
    name="graphrag-validation-pipeline",
    description="Validate, update metadata, load, and gate graph artifact"
)
def graphrag_pipeline():
    """Main pipeline definition."""
    
    # Step 1: Validate graph
    validate_task = validate_graph_op()
    
    # Step 2: Update/verify metadata (depends on validation)
    metadata_task = update_metadata_op()
    metadata_task.after(validate_task)
    
    # Step 3: Load graph (depends on metadata verification)
    load_task = load_graph_op()
    load_task.after(metadata_task)
    
    # Step 4: Run eval gate (depends on load)
    eval_task = eval_op()
    eval_task.after(load_task)


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

