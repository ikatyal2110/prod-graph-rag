#!/usr/bin/env python3
"""
Evaluation script for GraphRAG /query endpoint.

Evaluates retrieval quality against golden queries.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)


def read_golden_queries(filepath: str) -> List[Dict[str, Any]]:
    """Read golden queries from JSONL file."""
    queries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if 'query' not in obj or 'expected_incident_ids' not in obj:
                        print(f"Warning: Line {line_num} missing required fields, skipping", file=sys.stderr)
                        continue
                    queries.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON on line {line_num}: {e}", file=sys.stderr)
                    sys.exit(2)
    except FileNotFoundError:
        print(f"Error: Golden queries file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error reading golden queries file: {e}", file=sys.stderr)
        sys.exit(2)
    
    return queries


def query_api(base_url: str, question: str) -> Tuple[List[str], bool]:
    """
    Query the /query endpoint.
    
    Returns:
        (predicted_incident_ids, success_flag)
    """
    url = f"{base_url}/query"
    payload = {"question": question}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract evidence.incident_ids
        if 'evidence' in data and isinstance(data['evidence'], dict):
            incident_ids = data['evidence'].get('incident_ids', [])
            if isinstance(incident_ids, list):
                # Ensure all are strings
                return [str(id) for id in incident_ids], True
            else:
                print(f"Warning: evidence.incident_ids is not a list, got {type(incident_ids)}", file=sys.stderr)
                return [], True
        else:
            # Missing evidence field, treat as empty
            return [], True
            
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}", file=sys.stderr)
        return [], False
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except Exception as e:
        print(f"Error: Unexpected error for query: {question[:50]}...: {e}", file=sys.stderr)
        return [], False


def check_api_health(base_url: str) -> bool:
    """Check if API is reachable."""
    try:
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        return True
    except Exception:
        return False


def evaluate_queries(base_url: str, golden_queries: List[Dict[str, Any]], k: int) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Evaluate queries against API.
    
    Returns:
        (failures_list, correct_at_1_count, hits_at_k_count)
    """
    failures = []
    correct_at_1 = 0
    hits_at_k = 0
    
    # Check API health first
    if not check_api_health(base_url):
        print(f"Error: API at {base_url} is not reachable. Check /health endpoint.", file=sys.stderr)
        sys.exit(2)
    
    print(f"Evaluating {len(golden_queries)} queries against {base_url}...")
    
    for item in golden_queries:
        query = item['query']
        expected_ids = [str(id) for id in item['expected_incident_ids']]
        
        # Query API
        predicted_ids, success = query_api(base_url, query)
        
        if not success:
            # If query failed completely, record as failure with empty predictions
            predicted_ids = []
        
        # Get top-k slice
        top_k_predicted = predicted_ids[:k] if len(predicted_ids) >= k else predicted_ids
        
        # Calculate metrics for this query
        top1_correct = len(predicted_ids) > 0 and predicted_ids[0] in expected_ids
        hit_at_k = any(pred_id in expected_ids for pred_id in top_k_predicted)
        
        # Update counters
        if top1_correct:
            correct_at_1 += 1
        if hit_at_k:
            hits_at_k += 1
        
        # Record failure if not correct
        if not top1_correct or not hit_at_k:
            failures.append({
                "query": query,
                "expected_incident_ids": expected_ids,
                "predicted_incident_ids": predicted_ids,
                "top1_correct": top1_correct,
                "hit_at_k": hit_at_k
            })
    
    return failures, correct_at_1, hits_at_k


def write_results(output_file: str, base_url: str, k: int, n: int, 
                  accuracy_at_1: float, recall_at_k: float, failures: List[Dict[str, Any]]):
    """Write evaluation results to JSON file."""
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "base_url": base_url,
        "k": k,
        "n": n,
        "accuracy_at_1": accuracy_at_1,
        "recall_at_k": recall_at_k,
        "failures": failures
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing results file: {e}", file=sys.stderr)
        sys.exit(2)


def print_summary(n: int, accuracy_at_1: float, recall_at_k: float, failures: List[Dict[str, Any]]):
    """Print evaluation summary and failures."""
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Total queries: {n}")
    print(f"Accuracy@1: {accuracy_at_1:.4f} ({accuracy_at_1 * 100:.2f}%)")
    print(f"Recall@k: {recall_at_k:.4f} ({recall_at_k * 100:.2f}%)")
    print(f"Failures: {len(failures)}")
    
    if failures:
        print("\nFirst up to 5 failures:")
        print("-" * 60)
        for i, failure in enumerate(failures[:5], 1):
            print(f"\nFailure {i}:")
            print(f"  Query: {failure['query']}")
            print(f"  Expected: {failure['expected_incident_ids']}")
            print(f"  Predicted: {failure['predicted_incident_ids']}")
            print(f"  Top1 correct: {failure['top1_correct']}")
            print(f"  Hit@k: {failure['hit_at_k']}")
    print("=" * 60)


def get_output_filename(gold_file: str) -> str:
    """Generate output filename from golden file path."""
    import os
    base_name = os.path.basename(gold_file)
    stem = os.path.splitext(base_name)[0]  # Remove .jsonl extension
    return f"eval/results_{stem}.json"


def evaluate_single_file(base_url: str, gold_file: str, k: int) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluate a single golden file and return results.
    
    Returns:
        (output_file, results_dict)
    """
    # Read golden queries
    golden_queries = read_golden_queries(gold_file)
    if not golden_queries:
        print(f"Error: No valid queries found in {gold_file}", file=sys.stderr)
        sys.exit(2)
    
    n = len(golden_queries)
    
    # Evaluate queries
    failures, correct_at_1, hits_at_k = evaluate_queries(base_url, golden_queries, k)
    
    # Calculate metrics
    accuracy_at_1 = correct_at_1 / n if n > 0 else 0.0
    recall_at_k = hits_at_k / n if n > 0 else 0.0
    
    # Generate output filename
    output_file = get_output_filename(gold_file)
    
    # Prepare results
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "base_url": base_url,
        "k": k,
        "n": n,
        "accuracy_at_1": accuracy_at_1,
        "recall_at_k": recall_at_k,
        "failures": failures
    }
    
    # Write results
    write_results(output_file, base_url, k, n, accuracy_at_1, recall_at_k, failures)
    
    return output_file, results


def print_combined_summary(all_results: List[Tuple[str, Dict[str, Any]]]):
    """Print combined summary for multiple evaluation files."""
    print("\n" + "=" * 70)
    print("Combined Evaluation Summary")
    print("=" * 70)
    
    total_failures = 0
    for gold_file, results in all_results:
        n = results['n']
        accuracy_at_1 = results['accuracy_at_1']
        recall_at_k = results['recall_at_k']
        failures_count = len(results['failures'])
        total_failures += failures_count
        
        print(f"\n{gold_file}:")
        print(f"  Total queries: {n}")
        print(f"  Accuracy@1: {accuracy_at_1:.4f} ({accuracy_at_1 * 100:.2f}%)")
        print(f"  Recall@k: {recall_at_k:.4f} ({recall_at_k * 100:.2f}%)")
        print(f"  Failures: {failures_count}")
        
        # Print first 3 failures for this file
        if results['failures']:
            print(f"  First failures:")
            for i, failure in enumerate(results['failures'][:3], 1):
                print(f"    {i}. Query: {failure['query'][:60]}...")
                print(f"       Expected: {failure['expected_incident_ids']}, "
                      f"Predicted: {failure['predicted_incident_ids'][:3]}")
    
    print("\n" + "=" * 70)
    print(f"Total failures across all files: {total_failures}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate GraphRAG /query endpoint against golden queries"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of the API (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Value of k for recall@k metric (default: 5)"
    )
    parser.add_argument(
        "--gold",
        type=str,
        action="append",
        default=None,
        help="Path to golden queries JSONL file (can be provided multiple times)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Path to output results JSON file (deprecated: auto-generated from gold file name)"
    )
    
    args = parser.parse_args()
    
    # Validate k
    if args.k < 1:
        print("Error: --k must be >= 1", file=sys.stderr)
        sys.exit(2)
    
    # Determine which golden files to use
    if args.gold:
        gold_files = args.gold
    else:
        # Default behavior: use single default file
        gold_files = ["eval/golden_queries.jsonl"]
    
    # Check API health once before starting
    if not check_api_health(args.base_url):
        print(f"Error: API at {args.base_url} is not reachable. Check /health endpoint.", file=sys.stderr)
        sys.exit(2)
    
    # Evaluate each file
    all_results = []
    all_output_files = []
    
    for gold_file in gold_files:
        print(f"\n{'='*70}")
        print(f"Evaluating: {gold_file}")
        print(f"{'='*70}")
        
        output_file, results = evaluate_single_file(args.base_url, gold_file, args.k)
        all_results.append((gold_file, results))
        all_output_files.append(output_file)
        
        # Print summary for this file
        print_summary(results['n'], results['accuracy_at_1'], results['recall_at_k'], results['failures'])
    
    # Print combined summary if multiple files
    if len(gold_files) > 1:
        print_combined_summary(all_results)
    
    # Determine exit code: 0 if no failures in any file, 1 if any failures
    total_failures = sum(len(r['failures']) for _, r in all_results)
    exit_code = 0 if total_failures == 0 else 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

