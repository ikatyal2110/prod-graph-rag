#!/usr/bin/env python3
"""
Container component for evaluation gate.

This script runs the evaluation harness inside a container.
It expects the repo workspace to be mounted at /workspace.
It runs both golden query files and fails if any evaluation failures occur.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run evaluation gate."""
    api_base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
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
        capture_output=False
    )
    
    if result1.returncode != 0:
        print(f"\n✗ Evaluation failed on golden_queries.jsonl (exit code {result1.returncode})", file=sys.stderr)
        sys.exit(1)
    
    # Run second eval set
    print("\nRunning eval/golden_queries_hard.jsonl...")
    result2 = subprocess.run(
        [sys.executable, str(eval_script), "--gold", str(golden_queries_hard), "--k", "5", "--base-url", api_base_url],
        cwd=str(workspace),
        capture_output=False
    )
    
    if result2.returncode != 0:
        print(f"\n✗ Evaluation failed on golden_queries_hard.jsonl (exit code {result2.returncode})", file=sys.stderr)
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ Evaluation gate passed - all queries succeeded")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()

